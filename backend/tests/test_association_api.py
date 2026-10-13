import requests
import json


# =====================================================
# CONFIGURATION
# =====================================================

API_URL = "http://127.0.0.1:5000/association-test"


# =====================================================
# TEST 1: Gender vs Culture Result
# =====================================================

payload = {

    "district": "all",

    "block": "all",

    "sample_type": "all",

    "organisms": [],

    "independent_variable": "gender",

    "dependent_variable": "culture_result",

    "antibiotics": []

}


# =====================================================
# SEND POST REQUEST
# =====================================================

response = requests.post(

    API_URL,

    json=payload

)


print("\nSTATUS CODE:")
print(response.status_code)


print("\nRESPONSE:")
print(
    json.dumps(
        response.json(),
        indent=4
    )
)