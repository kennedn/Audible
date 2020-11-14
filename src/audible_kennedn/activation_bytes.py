import base64
import binascii
import hashlib
import pathlib
from urllib.parse import parse_qs

import httpx


def get_player_id(serial=None):
    if serial is None:
        player_id = hashlib.sha1(b"").digest()
    else:
        player_id = serial.encode().ljust(20, b'\0')[:20]

    return base64.encodebytes(player_id).rstrip().decode('ascii')


def extract_token_from_url(url):
    parsed_url = url.query
    query_dict = parse_qs(parsed_url)
    return query_dict["playerToken"]


def get_player_token(auth, serial=None) -> str:
    with httpx.Client(cookies=auth.website_cookies) as session:
        audible_base_url = f"https://www.audible.{auth.locale.domain}"
        params = {
            "ipRedirectOverride": True,
            "playerType": "software",
            "bp_ua": "y",
            "playerModel": "Desktop",
            "playerId": get_player_id(serial),
            "playerManufacturer": "Audible",
            "serial": ""
        }
        resp = session.get(f"{audible_base_url}/player-auth-token",
                           params=params)

        player_token = extract_token_from_url(resp.url)[0]

        return player_token


def fetch_activation(player_token):

    base_url_license = "https://www.audible.com"
    rurl = base_url_license + "/license/licenseForCustomerToken"
    # register params
    params = {
        "customer_token": player_token
    }
    # deregister params
    dparams = {
        "customer_token": player_token,
        "action": "de-register"
    }

    headers = {
        "User-Agent": "Audible Download Manager"
    }

    with httpx.Client(headers=headers) as session:
        session.get(rurl, params=dparams)

        resp = session.get(rurl, params=params)
        register_response_content = resp.content

        session.get(rurl, params=dparams)

        return register_response_content


def get_activation(auth, serial=None):

    player_token = get_player_token(auth, serial)
    activation_bytes = fetch_activation(player_token)

    return activation_bytes
