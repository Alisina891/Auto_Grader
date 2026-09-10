export const API_BASE_URL =
  "https://auto-grader-82jf.onrender.com";

export async function gradeStudentExcel(
  grade: string,
  projectId: string,
  studentName: string,
  attendanceNumber: string,
  email: string,
  file: File
) {
  const formData = new FormData();

  formData.append("file", file);

  const url =
    `${API_BASE_URL}/grade/${encodeURIComponent(grade)}/excel` +
    `?project_id=${encodeURIComponent(projectId)}` +
    `&student_name=${encodeURIComponent(studentName)}` +
    `&attendance_number=${encodeURIComponent(attendanceNumber)}` +
    `&email=${encodeURIComponent(email)}`;

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      "پاسخ نامعتبر از سرور دریافت شد."
    );
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "بررسی پروژه با خطا مواجه شد."
    );
  }

  return data;
}

export async function createTeacherProject(
  projectId: string,
  file: File
) {
  const formData = new FormData();

  formData.append("file", file);

  const url =
    `${API_BASE_URL}/teacher/create-project` +
    `?project_id=${encodeURIComponent(projectId)}`;

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      "پاسخ نامعتبر از سرور دریافت شد."
    );
  }

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "ایجاد پروژه با خطا مواجه شد."
    );
  }

  return data;
}