# Copyright 2020 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Graph plugin for AWS CloudTrail events."""

from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class CloudTrailGraph(BaseGraphPlugin):
    """Graph plugin for AWS CloudTrail events."""

    NAME = "CloudTrailEvents"
    DISPLAY_NAME = "AWS CloudTrail Events"

    def generate(self):
        """Generate the graph.

        Returns:
            Graph object instance.
        """
        query = 'data_type:"aws:cloudtrail:entry"'
        return_fields = [
            "event_name", "user_identity_arn", "user_name" ,"resources"
        ]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        for event in events:
            event_name = event["_source"].get("event_name")
            user_identity_arn = event["_source"].get("user_identity_arn")
            user_name = event["_source"].get("user_name")
            resources = event["_source"].get("resources")

            if not user_identity_arn or not event_name or not user_name or not resources:
                continue

            user_node = self.graph.add_node(user_name, {"type": "user", "arn": user_identity_arn})
            event_node = self.graph.add_node(
                resources, {"type": "resource", "resources": resources}
            )

            # Create edges between user and event
            self.graph.add_edge(user_node, event_node, event_name, event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(CloudTrailGraph)
