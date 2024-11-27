import requests
import urllib


class RORAPIHandler:
    API_URL = "https://api.ror.org/v2/organizations"

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

    def fetch(self, ror_id):
        """
        Query the ROR API for an organization with the given ROR ID
        and return the JSON result.
        """
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
    def organization_from_ror_id(ror_id):
        """
        Returns a dictionary of Organization model fields as returned by the ROR API.
        """

        def _first_name(result, **kwargs):
            first_name = None
            for name in result.get("names", []):
                # Validate all kwarg filters
                filters = []
                for k, v in kwargs.items():
                    if k.endswith("__not"):
                        filters.append(name[k[:-5]] != v)
                    elif k.endswith("__in"):
                        filters.append(v in name[k[:-4]])
                    else:
                        filters.append(name[k] == v)

                first_name = name["value"] if all(filters) else first_name
            return first_name

        result = RORAPIHandler().fetch(ror_id)
        if result == {}:
            return {}

        geonames = result.get("locations", [{}])[0].get("geonames_details", {})
        organization_fields = {
            "ror_json": result,
            "name": _first_name(result, types__in="ror_display"),
            "name_original": _first_name(result, types__in="label", lang__not="en"),
            "acronym": _first_name(result, types__in="acronym"),
            "country": geonames.get("country_code"),
            "address": geonames.get("name"),
        }

        return organization_fields

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
