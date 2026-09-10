const form = document.getElementById("gradeForm");

const loading = document.getElementById("loading");
const result = document.getElementById("result");

const scoreElement = document.getElementById("score");
const statusElement = document.getElementById("status");
const feedbackElement = document.getElementById("feedback");

const driveSection = document.getElementById("driveSection");
const driveLink = document.getElementById("driveLink");

const submitButton = document.getElementById("submitButton");


// ============================================================
// GET GRADE FROM URL
// ============================================================

function getGradeFromURL() {

    const pathParts =
        window.location.pathname
            .split("/")
            .filter(Boolean);

    const gradeIndex =
        pathParts.indexOf("grade");

    if (
        gradeIndex !== -1 &&
        pathParts.length > gradeIndex + 1
    ) {

        return pathParts[gradeIndex + 1]
            .trim()
            .toUpperCase();
    }

    return "";
}


const grade =
    getGradeFromURL();


// ============================================================
// SET HIDDEN GRADE INPUT
// ============================================================

const gradeInput =
    document.getElementById("grade");

if (gradeInput) {

    gradeInput.value =
        grade;
}


// ============================================================
// OPTIONAL GRADE DISPLAY
// ============================================================

const gradeDisplay =
    document.getElementById("gradeDisplay");

if (
    gradeDisplay &&
    grade
) {

    gradeDisplay.textContent =
        grade;
}


// ============================================================
// AI FEEDBACK
// ============================================================

function getAIFeedback(aiFeedback) {

    if (
        aiFeedback === null ||
        aiFeedback === undefined
    ) {

        return "";
    }


    // --------------------------------------------------------
    // Plain string
    // --------------------------------------------------------

    if (
        typeof aiFeedback === "string"
    ) {

        return aiFeedback.trim();
    }


    // --------------------------------------------------------
    // Object
    // --------------------------------------------------------

    if (
        typeof aiFeedback === "object"
    ) {

        // ----------------------------------------------------
        // Backend may return:
        //
        // {
        //     "ai_feedback": "..."
        // }
        // ----------------------------------------------------

        if (
            typeof aiFeedback.ai_feedback === "string" &&
            aiFeedback.ai_feedback.trim() !== ""
        ) {

            return aiFeedback.ai_feedback.trim();
        }


        // ----------------------------------------------------
        // Other possible text fields
        // ----------------------------------------------------

        const possibleFields = [
            "feedback",
            "message",
            "text",
            "output_text",
            "content"
        ];


        for (
            const field
            of possibleFields
        ) {

            if (
                typeof aiFeedback[field] === "string" &&
                aiFeedback[field].trim() !== ""
            ) {

                return aiFeedback[field].trim();
            }
        }


        // ----------------------------------------------------
        // OpenAI / Groq output structure
        // ----------------------------------------------------

        if (
            Array.isArray(
                aiFeedback.output
            )
        ) {

            const texts = [];


            for (
                const outputItem
                of aiFeedback.output
            ) {

                if (
                    outputItem &&
                    Array.isArray(
                        outputItem.content
                    )
                ) {

                    for (
                        const contentItem
                        of outputItem.content
                    ) {

                        if (
                            contentItem &&
                            typeof contentItem.text === "string"
                        ) {

                            texts.push(
                                contentItem.text
                            );
                        }
                    }
                }
            }


            if (
                texts.length > 0
            ) {

                return texts.join(
                    "\n\n"
                );
            }
        }


        // ----------------------------------------------------
        // Final fallback
        // ----------------------------------------------------

        try {

            return JSON.stringify(
                aiFeedback,
                null,
                2
            );

        }
        catch (error) {

            return "";
        }
    }


    return "";
}


// ============================================================
// DETERMINISTIC FEEDBACK
// ============================================================

function getDeterministicFeedback(
    feedbackItems
) {

    if (
        !Array.isArray(
            feedbackItems
        )
    ) {

        return "";
    }


    return feedbackItems
        .map(item => {

            if (
                typeof item === "string"
            ) {

                return item;
            }


            if (
                item &&
                typeof item === "object"
            ) {

                return item.message || "";
            }


            return "";

        })
        .filter(
            message =>
                typeof message === "string" &&
                message.trim() !== ""
        )
        .join("\n\n");
}


// ============================================================
// STATUS
// ============================================================

function updateStatus(status) {

    if (!statusElement) {

        return;
    }


    statusElement.textContent =
        status || "نامشخص";


    // --------------------------------------------------------
    // Remove old classes
    // --------------------------------------------------------

    statusElement.classList.remove(
        "status-passed",
        "status-failed"
    );


    if (!status) {

        return;
    }


    const normalizedStatus =
        String(status).toLowerCase();


    // --------------------------------------------------------
    // Passed
    // --------------------------------------------------------

    if (
        normalizedStatus.includes("pass") ||
        normalizedStatus.includes("قبول") ||
        normalizedStatus.includes("موفق")
    ) {

        statusElement.classList.add(
            "status-passed"
        );

        return;
    }


    // --------------------------------------------------------
    // Failed
    // --------------------------------------------------------

    if (
        normalizedStatus.includes("fail") ||
        normalizedStatus.includes("رد") ||
        normalizedStatus.includes("مردود")
    ) {

        statusElement.classList.add(
            "status-failed"
        );
    }
}


// ============================================================
// RESET RESULT
// ============================================================

function resetResult() {

    if (scoreElement) {

        scoreElement.textContent =
            "-";
    }


    if (statusElement) {

        statusElement.textContent =
            "-";

        statusElement.classList.remove(
            "status-passed",
            "status-failed"
        );
    }


    if (feedbackElement) {

        feedbackElement.textContent =
            "-";
    }


    if (driveSection) {

        driveSection.classList.add(
            "hidden"
        );
    }


    if (driveLink) {

        driveLink.href =
            "#";
    }
}


// ============================================================
// FORM CHECK
// ============================================================

if (!form) {

    console.error(
        "gradeForm was not found."
    );

}
else {

    // ========================================================
    // FORM SUBMISSION
    // ========================================================

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            // ------------------------------------------------
            // Get inputs
            // ------------------------------------------------

            const studentNameInput =
                document.getElementById(
                    "studentName"
                );
            
            const emailInput =
            document.getElementById(
                "email"
            );

            const attendanceInput =
                document.getElementById(
                    "attendanceNumber"
                );


            const projectInput =
                document.getElementById(
                    "projectId"
                );


            const fileInput =
                document.getElementById(
                    "excelFile"
                );


            const studentName =
                studentNameInput
                    ? studentNameInput.value.trim()
                    : "";

            
            const email =
                emailInput
                    ? emailInput.value.trim().toLowerCase()
                    : "";
            const attendanceNumber =
                attendanceInput
                    ? attendanceInput.value.trim()
                    : "";


            const projectId =
                projectInput
                    ? projectInput.value.trim()
                    : "";


            const file =
                fileInput &&
                fileInput.files.length > 0
                    ? fileInput.files[0]
                    : null;


            // ------------------------------------------------
            // Validate grade
            // ------------------------------------------------

            if (!grade) {

                alert(
                    "نمره صنف از لینک صفحه دریافت نشد. لطفاً لینک صنف خود را بررسی کنید."
                );

                return;
            }


            // ------------------------------------------------
            // Validate student name
            // ------------------------------------------------

            if (!studentName) {

                alert(
                    "لطفاً نام و تخلص خود را وارد کنید."
                );

                if (studentNameInput) {

                    studentNameInput.focus();
                }

                return;
            }

            // ------------------------------------------------
// Validate email
// ------------------------------------------------

            if (!email) {

                alert(
                    "لطفاً ایمیل خود را وارد کنید."
                );

                if (emailInput) {
                    emailInput.focus();
                }

                return;
            }


            const emailPattern =
                /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


            if (!emailPattern.test(email)) {

                alert(
                    "لطفاً یک ایمیل معتبر وارد کنید."
                );

                if (emailInput) {
                    emailInput.focus();
                }

                return;
            }


            // ------------------------------------------------
            // Validate attendance
            // ------------------------------------------------

            if (!attendanceNumber) {

                alert(
                    "لطفاً شماره حاضری خود را وارد کنید."
                );

                if (attendanceInput) {

                    attendanceInput.focus();
                }

                return;
            }


            // ------------------------------------------------
            // Validate project
            // ------------------------------------------------

            if (!projectId) {

                alert(
                    "لطفاً شماره پروژه را وارد کنید."
                );

                if (projectInput) {

                    projectInput.focus();
                }

                return;
            }


            // ------------------------------------------------
            // Validate file
            // ------------------------------------------------

            if (!file) {

                alert(
                    "لطفاً فایل Excel پروژه را انتخاب کنید."
                );

                if (fileInput) {

                    fileInput.focus();
                }

                return;
            }


            // ------------------------------------------------
            // Check Excel extension
            // ------------------------------------------------

            const fileName =
                file.name.toLowerCase();


            const validExtension =
                fileName.endsWith(".xlsx") ||
                fileName.endsWith(".xlsm");


            if (!validExtension) {

                alert(
                    "لطفاً یک فایل Excel معتبر با پسوند .xlsx یا .xlsm انتخاب کنید."
                );

                return;
            }


            // ------------------------------------------------
            // FormData
            // ------------------------------------------------

            const formData =
                new FormData();


            formData.append(
                "file",
                file
            );


            // ------------------------------------------------
            // Reset previous result
            // ------------------------------------------------

            resetResult();


            // ------------------------------------------------
            // Show loading
            // ------------------------------------------------

            if (loading) {

                loading.classList.remove(
                    "hidden"
                );
            }


            if (result) {

                result.classList.add(
                    "hidden"
                );
            }


            // ------------------------------------------------
            // Disable submit button
            // ------------------------------------------------

            if (submitButton) {

                submitButton.disabled =
                    true;

                submitButton.textContent =
                    "در حال بررسی پروژه...";
            }


            try {

                // =================================================
                // BUILD API URL
                // =================================================

                const apiURL =
                    `/grade/${encodeURIComponent(grade)}/excel` +
                    `?project_id=${encodeURIComponent(projectId)}` +
                    `&student_name=${encodeURIComponent(studentName)}` +
                    `&email=${encodeURIComponent(email)}` +
                    `&attendance_number=${encodeURIComponent(attendanceNumber)}`;


                // =================================================
                // SEND REQUEST
                // =================================================

                const response =
                    await fetch(
                        apiURL,
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                // =================================================
                // READ RESPONSE
                // =================================================

                let data;


                try {

                    data =
                        await response.json();

                }
                catch (jsonError) {

                    throw new Error(
                        "پاسخ نامعتبر از سرور دریافت شد."
                    );
                }


                // =================================================
                // API ERROR
                // =================================================

                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "بررسی پروژه با خطا مواجه شد."
                    );
                }


                // =================================================
                // SCORE
                // =================================================

                if (
                    data.score !== null &&
                    data.score !== undefined
                ) {

                    if (data.max_score !== null &&
                        data.max_score !== undefined) {

                        scoreElement.textContent =
                            `${data.score} / ${data.max_score}`;

                    }
                    else {

                        scoreElement.textContent =
                            data.score;
                    }

                }
                else {

                    scoreElement.textContent =
                        "-";
                }


                // =================================================
                // STATUS
                // =================================================

                updateStatus(
                    data.status
                );


                // =================================================
                // AI FEEDBACK
                // =================================================

                const aiFeedback =
                    getAIFeedback(
                        data.ai_feedback
                    );


                // =================================================
                // DETERMINISTIC FEEDBACK
                // =================================================

                const deterministicFeedback =
                    getDeterministicFeedback(
                        data.student_feedback
                    );


                // =================================================
                // DISPLAY FEEDBACK
                // =================================================

                if (aiFeedback) {

                    feedbackElement.textContent =
                        aiFeedback;

                }
                else if (
                    deterministicFeedback
                ) {

                    feedbackElement.textContent =
                        deterministicFeedback;

                }
                else {

                    feedbackElement.textContent =
                        "برای این پروژه بازخوردی ثبت نشده است.";
                }


                // =================================================
                // GOOGLE DRIVE
                // =================================================

                if (
                    data.google_drive &&
                    data.google_drive.uploaded &&
                    data.google_drive.web_view_link
                ) {

                    if (driveSection) {

                        driveSection.classList.remove(
                            "hidden"
                        );
                    }


                    if (driveLink) {

                        driveLink.href =
                            data.google_drive.web_view_link;
                    }

                }
                else {

                    if (driveSection) {

                        driveSection.classList.add(
                            "hidden"
                        );
                    }


                    if (driveLink) {

                        driveLink.href =
                            "#";
                    }
                }


                // =================================================
                // SHOW RESULT
                // =================================================

                if (result) {

                    result.classList.remove(
                        "hidden"
                    );
                }


                // =================================================
                // SCROLL TO RESULT
                // =================================================

                setTimeout(
                    () => {

                        if (result) {

                            result.scrollIntoView({
                                behavior: "smooth",
                                block: "start"
                            });
                        }

                    },
                    100
                );


            }
            catch (error) {

                console.error(
                    "Grading Error:",
                    error
                );


                alert(
                    "خطا در بررسی پروژه:\n\n" +
                    error.message
                );

            }
            finally {

                // ------------------------------------------------
                // Hide loading
                // ------------------------------------------------

                if (loading) {

                    loading.classList.add(
                        "hidden"
                    );
                }


                // ------------------------------------------------
                // Enable submit button
                // ------------------------------------------------

                if (submitButton) {

                    submitButton.disabled =
                        false;

                    submitButton.textContent =
                        "بررسی و نمره‌دهی پروژه";
                }
            }

        }
    );
}