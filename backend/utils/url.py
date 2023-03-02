def _get_google_maps_link(address: str) -> str:
    zip_code = address.split(", ")[1]
    return f"https://www.google.com/maps/search/?api=1&query={zip_code}&zoom=20"
