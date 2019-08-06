# Copyright (c) 2019 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import urllib
import requests
from pyincore import IncoreClient


class SpaceService:
    """
        Space service client
    """

    def __init__(self, client: IncoreClient):
        self.client = client
        self.base_space_url = urllib.parse.urljoin(client.service_url, "space/api/spaces/")

    def create_space(self, space_json):
        """
        Creates a Space
        Args:
            space_json: JSON representing a space

        Returns: JSON of the created space

        """
        url = self.base_space_url
        space_data = {('space', space_json)}

        r = requests.post(url, files=space_data, headers=self.client.headers)
        response = r.json()
        return response

    def get_spaces(self, dataset_id: str = None):
        url = self.base_space_url
        payload = {}
        if dataset_id is not None:
            payload['dataset'] = dataset_id

        r = requests.get(url, headers=self.client.headers, params=payload)
        response = r.json()

        return response

    def get_space_by_id(self, space_id: str):
        url = urllib.parse.urljoin(self.base_space_url, space_id)
        r = requests.get(url, headers=self.client.headers)
        response = r.json()

        return response

    def update_space(self, space_id: str, space_json):
        """
        Updates a Space
        Args:
            space_id : ID of the space to update
            space_json: JSON representing a space update

        Returns: JSON of the updated space

        """
        url = urllib.parse.urljoin(self.base_space_url, space_id)
        space_data = {('space', space_json)}

        r = requests.put(url, files=space_data, headers=self.client.headers)
        response = r.json()
        return response

    def add_dataset_to_space(self, space_id: str, dataset_id: str):
        url = urllib.parse.urljoin(self.base_space_url, space_id + "/datasets/" + dataset_id)

        r = requests.post(url, headers=self.client.headers)
        response = r.json()
        return response

    def grant_privileges_to_space(self, space_id: str, privileges_json):
        url = urllib.parse.urljoin(self.base_space_url, space_id + "/grant")
        space_privileges = {('grant', privileges_json)}

        r = requests.post(url, files=space_privileges, headers=self.client.headers)
        response = r.json()
        return response
