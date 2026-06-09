// String fields
let code = pm.iterationData.get("code") || "";
pm.environment.set("code", code);

let fullName = pm.iterationData.get("fullName") || "";
pm.environment.set("fullName", fullName);

let givenName = pm.iterationData.get("givenName") || "";
pm.environment.set("givenName", givenName);

let password = pm.iterationData.get("password") || "";
pm.environment.set("password", password);

let roleCode = pm.iterationData.get("roleCode") || "";
pm.environment.set("roleCode", roleCode);

let tenantCode = pm.iterationData.get("tenantCode") || "";
pm.environment.set("tenantCode", tenantCode);

let phoneNumber = pm.iterationData.get("phoneNumber") || "";
pm.environment.set("phoneNumber", phoneNumber);

let genderCode = pm.iterationData.get("genderCode") || "";
pm.environment.set("genderCode", genderCode);

let birthDate = pm.iterationData.get("birthDate") || "";
pm.environment.set("birthDate", birthDate);

let startWorkingAt = pm.iterationData.get("startWorkingAt") || "";
pm.environment.set("startWorkingAt", startWorkingAt);

let grade = pm.iterationData.get("grade") || "";
pm.environment.set("grade", grade);

let companyName = pm.iterationData.get("companyName") || "";
pm.environment.set("companyName", companyName);

let profileIcon = pm.iterationData.get("profileIcon") || "";
pm.environment.set("profileIcon", profileIcon);

let employeeId = pm.iterationData.get("employeeId") || "";
pm.environment.set("employeeId", employeeId);

let positionId = pm.iterationData.get("positionId") || "";
pm.environment.set("positionId", positionId);

let positionName = pm.iterationData.get("positionName") || "";
pm.environment.set("positionName", positionName);

let levelId = pm.iterationData.get("levelId") || "";
pm.environment.set("levelId", levelId);

let levelName = pm.iterationData.get("levelName") || "";
pm.environment.set("levelName", levelName);

let siteId = pm.iterationData.get("siteId") || "";
pm.environment.set("siteId", siteId);

let siteName = pm.iterationData.get("siteName") || "";
pm.environment.set("siteName", siteName);

let departmentId = pm.iterationData.get("departmentId") || "";
pm.environment.set("departmentId", departmentId);

let departmentName = pm.iterationData.get("departmentName") || "";
pm.environment.set("departmentName", departmentName);

let sectionId = pm.iterationData.get("sectionId") || "";
pm.environment.set("sectionId", sectionId);

let sectionName = pm.iterationData.get("sectionName") || "";
pm.environment.set("sectionName", sectionName);

// Number fields
let Age = pm.iterationData.get("Age");
pm.environment.set("Age", Age);

let AgeWorkingAt = pm.iterationData.get("AgeWorkingAt");
pm.environment.set("AgeWorkingAt", AgeWorkingAt);

// Boolean fields
let isExternal = pm.iterationData.get("isExternal");
pm.environment.set("isExternal", isExternal);

let isControlRoom = pm.iterationData.get("isControlRoom");
pm.environment.set("isControlRoom", isControlRoom);

// Nullable fields
let supervisorId = pm.iterationData.get("supervisorId") || null;
pm.environment.set("supervisorId", supervisorId);

let supervisorName = pm.iterationData.get("supervisorName") || null;
pm.environment.set("supervisorName", supervisorName);

let shiftId = pm.iterationData.get("shiftId") || null;
pm.environment.set("shiftId", shiftId);

let lastPositionName = pm.iterationData.get("lastPositionName") || null;
pm.environment.set("lastPositionName", lastPositionName);

let ageLastPosition = pm.iterationData.get("ageLastPosition") || null;
pm.environment.set("ageLastPosition", ageLastPosition);

// localStatus
let localStatus = "";
if (pm.iterationData.get("localStatus")) {
    localStatus = pm.iterationData.get("localStatus");
    // localStatus = JSON.stringify(localStatus);
}
pm.environment.set("localStatus", localStatus);
