from typing import Any
import requests
from urllib.parse import quote


class RORAPIHandler:
    API_URL = "https://api.ror.org/v2/organizations"

    def query(self, query_string: str, all_status: bool = True) -> dict[str, Any]:
        # URL-encode query_string to make it safe for use in a URL
        query_string = quote(query_string)

        url = f'{self.API_URL}?query="{query_string}"'
        if all_status:
            url += "&all_status"
        response = requests.get(url)
        try:
            data: dict[str, str] = response.json()
        except requests.JSONDecodeError:
            data = {}

        items = list(map(self._map_ror_to_organization, data.get("items", [])))
        return {**data, "items": items}

    def fetch(self, ror_id: str) -> dict[str, Any]:
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
            response = self._map_ror_to_organization(data)
        except (requests.JSONDecodeError, KeyError):
            response = {}

        return response

    @staticmethod
    def organization_from_ror_id(ror_id: str) -> dict[str, Any]:
        """
        Returns a dictionary of Organization model fields as returned by the ROR API.
        """

        def _first_name(result: dict[str, Any], **kwargs: str) -> str:
            """
            Returns the first name in the list of names that matches all kwargs filters.
            If no name matches, returns an empty string.
            """
            first_name = ""

            names: list[dict[str, str]] = result.get("names", [])
            for name in names:
                # Create filters for each kwarg
                filters: list[bool] = []
                for k, v in kwargs.items():
                    match k.split("__", 1):
                        case [key, "not"]:
                            filters.append(name[key] != v)
                        case [key, "in"]:
                            filters.append(v in name[key])
                        case _:
                            filters.append(name[k] == v)

                first_name = name["value"] if all(filters) else first_name
            return first_name

        result = RORAPIHandler().fetch(ror_id)

        location_details: dict[str, Any] = result.get("locations", [{}])[0].get(
            "geonames_details", {}
        )

        organization_fields = {
            "ror_json": result,
            "name": _first_name(result, types__in="ror_display"),
            "name_original": _first_name(result, types__in="label", lang__not="en"),
            "acronym": _first_name(result, types__in="acronym"),
            "country": location_details.get("country_code"),
            "address": location_details.get("name"),
        }

        return organization_fields

    @staticmethod
    def _map_ror_to_organization(data: dict[str, Any]) -> dict[str, Any]:
        """
        Processes an organization from the ROR API into a dict that can be used
        to create a new Organization object.
        """

        # Remove url part from ROR ID
        ror_link = data["id"]
        ror_id = ror_link.split("/")[-1]

        return {**data, "id": ror_id, "ror_link": ror_link}
