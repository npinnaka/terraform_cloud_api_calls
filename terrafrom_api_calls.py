from urllib3 import PoolManager
import json
import boto3

http = PoolManager()


def get_workspace_id(params):
    headers = {"Authorization": "Bearer " + params["TOKEN"],
               "Content-Type": "application/vnd.api+json"}
    url = "https://{tfe_host}/api/v2/organizations/{organization}/workspaces/{workspace}".format(**params)
    workspace_id = json.loads(http.request("GET", url, headers=headers).data)["data"]["id"]
    return {"workspace_id": workspace_id}


def get_workspace_vars(params):
    headers = {"Authorization": "Bearer " + params["TOKEN"],
               "Content-Type": "application/vnd.api+json"}
    get_params = dict((k, params[k]) for k in ("workspace_id", "tfe_host"))
    url = "https://{tfe_host}/api/v2/workspaces/{workspace_id}/vars".format(**get_params)
    response = json.loads(http.request("GET", url, headers=headers).data)
    vars = dict()
    for var in response["data"]:
        if (var["attributes"]["category"] == "terraform"):
            vars.update({var["attributes"]["key"]: var["id"]})
    print(vars)
    return vars


def update_workspace_vars(workspace_vars, var_values, params):
    headers = {"Authorization": "Bearer " + params["TOKEN"],
               "Content-Type": "application/vnd.api+json"}
    for k in var_values:
        payload = {
            "data": {
                "id": workspace_vars[k],
                "attributes": {
                    "key": k,
                    "value": var_values[k],
                    "category": "terraform"
                },
                "type": "vars"
            }
        }
        patch_params = dict((k, params[k]) for k in ("workspace_id", "tfe_host"))
        patch_params.update({"var_id": workspace_vars[k]})
        url = "https://{tfe_host}/api/v2/workspaces/{workspace_id}/vars/{var_id}".format(**patch_params)
        response = http.request("PATCH", url, headers=headers, body=payload).data


def get_upload_url(params):
    headers = {"Authorization": "Bearer " + params["TOKEN"],
               "Content-Type": "application/vnd.api+json"}
    post_params = dict((k, params[k]) for k in ("tfe_host", "workspace_id"))
    url = "https://{tfe_host}/api/v2/workspaces/{workspace_id}/configuration-versions".format(**post_params)
    payload = {"data": {"type": "configuration-versions", "attributes": {"auto-queue-runs": False}}}
    encoded_payload = json.dumps(payload).encode('utf-8')
    response = json.loads(http.request("POST", url, headers=headers, body=encoded_payload).data)["data"]
    return {"upload_url": response["attributes"]["upload-url"], "config_version_id": response["id"]}


def upload_configuration_tar_gz(params):
    headers = {"Authorization": "Bearer " + params["TOKEN"]}
    local_file = "/tmp/" + params["file_name"]
    s3 = boto3.resource("s3")
    s3.Bucket(params["bucket"]).download_file("emr/" + params["file_name"], local_file)
    try:
        file_stream = open(local_file, "rb").read()
        args = {
            "file": file_stream}
        response = http.request('PUT', params["upload_url"], args, headers)
    except Exception as e:
        print("exception occured during upload", e)
    except RuntimeError as r:
        print("runtime error occured", r)


def trigger_tfe_run(params):
    headers = {"Authorization": "Bearer " + params["TOKEN"],
               "Content-Type": "application/vnd.api+json"}
    payload = {
        "data": {
            "attributes": {
                "is-destroy": False,
                "message": "EMR Run is triggered",
            },
            "type": "runs",
            "relationships": {
                "workspace": {
                    "data": {
                        "type": "workspaces",
                        "id": params["workspace_id"]
                    }
                },
                "configuration-version": {
                    "data": {
                        "type": "configuration-versions",
                        "id": params["config_version_id"]
                    }
                }
            }
        }
    }
    encoded_payload = json.dumps(payload).encode('utf-8')
    post_params = dict({"tfe_host": params["tfe_host"]})
    url = "https://{tfe_host}/api/v2/runs".format(**post_params)
    response = json.loads(http.request("POST", url, headers=headers, body=encoded_payload).data)
    return response


def create_infrastructure(token, input):
    # input = {"file_name": "upload.tar", "bucket": "narendra-pinnaka-s3-bucket"}
    params = {"TOKEN": token,
              "tfe_host": "app.terraform.io",
              "organization": "pinnaka",
              "workspace": "training",
              "file_name": "upload.tar.gz",
              "bucket": "narendra-pinnaka-s3-bucket"}
    params.update(input)
    params.update(get_workspace_id(params))
    workspace_vars = get_workspace_vars(params)
    params.update(get_upload_url(params))
    update_workspace_vars(workspace_vars, input, params)
    upload_configuration_tar_gz(params)
    response = trigger_tfe_run(params)
    # print(response)


if __name__ == '__main__':
    create_infrastructure(
        "7Qq0NNW2w39D9A.atlasv1.S8puXugOKlfKu8jLPwSygxz5NflqmHxwBGUAP63lIcA66XUoI1htz1W9R2ksz84HTw0",
        {"prefixes": [["a"],["b"],["c"]]})
