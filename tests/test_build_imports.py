from target_conversion import (
    build_imports,
    ApiClientTarget,
    build_param_imports,
    build_request_imports,
)

one_test_target = ApiClientTarget(
    url_path="/notifications/behaviorGroups",
    verb="post",
    summary="Create a behavior group",
    operation_id="NotificationResource$V2_createBehaviorGroup",
    request_class="NotificationResourceV2CreateBehaviorGroup",
    request_schema="#/components/schemas/CreateBehaviorGroupRequest",
    request_schema_class="CreateBehaviorGroupRequest",
    response_schema="#/components/schemas/CreateBehaviorGroupResponse",
    response_schema_class="CreateBehaviorGroupResponse",
    parameter_schema="#/components/schemas/CreateBehaviorGroupRequest",
    parameter_class="CreateBehaviorGroupParams",
    parameter_api_client_call="createBehaviorGroupRequest",
    parameter_dependent_objects="const createBehaviorGroupRequest : "
    'CreateBehaviorGroupRequest = { displayName: "" };',
    expected_response="200",
    resolved_params=[],
)


def test_build_param_imports():
    imports_out = build_param_imports("Notification", "V2", [one_test_target])
    assert len(imports_out) == 1
    assert (
        imports_out[0]["importClass"]
        == "NotificationResourceV2CreateBehaviorGroupParams"
    )
    assert (
        imports_out[0]["importPackage"] == "NotificationResourceV2CreateBehaviorGroup"
    )


def test_build_request_imports():
    imports_out = build_request_imports("Notification", "V2", [one_test_target])
    assert len(imports_out) == 1
    assert imports_out[0]["importClass"] == "CreateBehaviorGroupRequest"
    assert imports_out[0]["importPackage"] == "types"


def test_build_imports():

    imports_out = build_imports("Notifications", "V2", "", [one_test_target])

    # Confirm the client import
    assert imports_out[0]["importClass"] == "NotificationsClient"
    assert imports_out[0]["importPackage"] == "api"

    # Confirm the parameter imports
    assert (
        imports_out[1]["importClass"]
        == "NotificationResourceV2CreateBehaviorGroupParams"
    )
    assert (
        imports_out[1]["importPackage"] == "NotificationResourceV2CreateBehaviorGroup"
    )

    # Confirm the request object imports
    assert imports_out[2]["importClass"] == "CreateBehaviorGroupRequest"
    assert imports_out[2]["importPackage"] == "types"

    assert len(imports_out) > 0
