"""Sketch analyzer plugin for aws cloudtrail."""

from __future__ import unicode_literals

import json
import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

logger = logging.getLogger("timesketch.analyzers.aws_cloudtrail")


class AwsCloudtrailSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for AwsCloudtrail."""

    NAME = "aws_cloudtrail"
    DISPLAY_NAME = "AWS CloudTrail Analyzer"
    DESCRIPTION = (
        "Extract features and tag security relevant actions in AWS CloudTrail."
    )

    DEPENDENCIES = frozenset()

    CLOUD_TRAIL_EVENT = "cloud_trail_event"
    EVENT_NAME = "event_name"

    def _parse_cloudtrail_event(self, event):
        """Parses the CloudTrail event string into a dictionary."""
        cloud_trail_event_str = event.source.get(self.CLOUD_TRAIL_EVENT)
        if not cloud_trail_event_str:
            return

        try:
            return json.loads(cloud_trail_event_str)
        except json.JSONDecodeError:
            return None

    def _cloudtrail_add_tag(self, event):
        """Tags CloudTrail events based on event details and type."""
        cloud_trail_event = self._parse_cloudtrail_event(event)
        event_name = event.source.get(self.EVENT_NAME)

        if cloud_trail_event:
            if cloud_trail_event.get("readOnly"):
                event.add_tags(["readOnly"])
                event.add_emojis([emojis.get_emoji("MAGNIFYING_GLASS")])

            if cloud_trail_event.get("errorCode") in [
                "UnauthorizedOperation",
                "AccessDenied",
            ]:
                event.add_tags(["UnauthorizedAPICall"])

            user_name = cloud_trail_event.get("userIdentity", {}).get("userName")
            error_message = cloud_trail_event.get("errorMessage")
            if (
                user_name == "HIDDEN_DUE_TO_SECURITY_REASONS"
                and error_message == "No username found in supplied account"
            ):
                event.add_tags(["FailedLoginNonExistentIAMUser"])

        if event_name:
            if event_name in (
                "AuthorizeSecurityGroupIngress",
                "AuthorizeSecurityGroupEgress",
                "RevokeSecurityGroupIngress",
                "RevokeSecurityGroupEgress",
                "CreateSecurityGroup",
                "DeleteSecurityGroup",
            ):
                event.add_tags(["SG"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateNetworkAcl",
                "CreateNetworkAclEntry",
                "DeleteNetworkAcl",
                "DeleteNetworkAclEntry",
                "ReplaceNetworkAclEntry",
                "ReplaceNetworkAclAssociation",
            ):
                event.add_tags(["NACL"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateCustomerGateway",
                "DeleteCustomerGateway",
                "AttachInternetGateway",
                "CreateInternetGateway",
                "DeleteInternetGateway",
                "DetachInternetGateway",
            ):
                event.add_tags(["GW"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateRoute",
                "CreateRouteTable",
                "ReplaceRoute",
                "ReplaceRouteTableAssociation",
                "DeleteRouteTable",
                "DeleteRoute",
                "DisassociateRouteTable",
            ):
                event.add_tags(["RouteTable"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateVpc",
                "DeleteVpc",
                "ModifyVpcAttribute",
                "AcceptVpcPeeringConnection",
                "CreateVpcPeeringConnection",
                "DeleteVpcPeeringConnection",
                "RejectVpcPeeringConnection",
                "AttachClassicLinkVpc",
                "DetachClassicLinkVpc",
                "DisableVpcClassicLink",
                "EnableVpcClassicLink",
            ):
                event.add_tags(["VPC"])
                event.add_tags(["NetworkChanged"])

            if event_name in (
                "PutGroupPolicy",
                "PutRolePolicy",
                "PutUserPolicy",
                "AttachGroupPolicy",
                "AttachRolePolicy",
                "AttachUserPolicy",
                "CreatePolicyVersion",
                "SetDefaultPolicyVersion",
                "AddUserToGroup",
                "CreateLoginProfile",
                "UpdateLoginProfile",
                "CreateAccessKey",
                "CreateRole",
                "AssumeRole",
            ):
                event.add_tags(["SuspicousIAMActivity"])

            if event_name == "ConsoleLogin":
                event.add_tags(["ConsoleLogin"])

            if event_name == "GetCallerIdentity":
                event.add_tags(["GetCallerIdentity"])

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'data_type:"aws:cloudtrail:entry"'

        return_fields = [self.CLOUD_TRAIL_EVENT, self.EVENT_NAME]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        for event in events:
            self._cloudtrail_add_tag(event)
            event.commit()

        return "AWS CloudTrail Analyzer completed"


manager.AnalysisManager.register_analyzer(AwsCloudtrailSketchPlugin)
