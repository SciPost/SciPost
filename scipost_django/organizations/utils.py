import requests
import urllib


class RORAPIHandler:
    API_URL = "https://api.ror.org/organizations"

    def query(self, query_string, all_status=True):
        # URL-encode query_string to make it safe for use in a URL
        query_string = urllib.parse.quote(query_string)

        url = f'{self.API_URL}?query="{query_string}"'
        if all_status:
            url += "&all_status"
        response = requests.get(url)
        data = response.json()

        items = list(map(self._process_organization, data["items"]))
        return {**data, "items": items}

    def from_id(self, ror_id):
        # For old grid IDs, use a query instead
        # and only return a result if there is exactly one
        if ror_id.startswith("grid"):
            results = self.query(ror_id)
            if results["number_of_results"] != 1:
                return {}
            else:
                return results["items"][0]

        # Handle ROR IDs normally
        url = f"{self.API_URL}/{ror_id}"
        response = requests.get(url)
        try:
            data = response.json()
            response = self._process_organization(data)
        except:
            response = {}

        return response

    @staticmethod
    def _process_organization(organization):
        """
        Processes an organization from the ROR API into a dict that can be used
        to create a new Organization object.
        """

        # Remove url part from ROR ID
        ror_link = organization["id"]
        ror_id = ror_link.split("/")[-1]

        return {**organization, "id": ror_id, "ror_link": ror_link}
