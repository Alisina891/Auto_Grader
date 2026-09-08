
const form = document.getElementById("teacherForm");

const projectIdInput =
    document.getElementById("projectId");

const masterFileInput =
    document.getElementById("masterFile");

const loading =
    document.getElementById("loading");

const successResult =
    document.getElementById("successResult");

const resultProjectId =
    document.getElementById("resultProjectId");

const resultFileName =
    document.getElementById("resultFileName");

const createButton =
    document.getElementById("createButton");


// ============================================================
// FORM SUBMISSION
// ============================================================

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        // ----------------------------------------------------
        // Get values
        // ----------------------------------------------------

        const projectId =
            projectIdInput.value.trim();

        const file =
            masterFileInput.files[0];


        // ----------------------------------------------------
        // Validation
        // ----------------------------------------------------

        if (!projectId) {

            alert(
                "لطفاً شماره پروژه را وارد کنید."
            );

            return;
        }


        if (!file) {

            alert(
                "لطفاً فایل Master پروژه را انتخاب کنید."
            );

            return;
        }


        // ----------------------------------------------------
        // Check Excel extension
        // ----------------------------------------------------

        const fileName =
            file.name.toLowerCase();

        const validExtension =
            fileName.endsWith(".xlsx") ||
            fileName.endsWith(".xlsm");


        if (!validExtension) {

            alert(
                "لطفاً یک فایل Excel معتبر انتخاب کنید."
            );

            return;
        }


        // ----------------------------------------------------
        // FormData
        // ----------------------------------------------------

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );


        // ----------------------------------------------------
        // Reset previous result
        // ----------------------------------------------------

        successResult.classList.add(
            "hidden"
        );


        // ----------------------------------------------------
        // Show loading
        // ----------------------------------------------------

        loading.classList.remove(
            "hidden"
        );


        // ----------------------------------------------------
        // Disable button
        // ----------------------------------------------------

        createButton.disabled = true;

        createButton.textContent =
            "در حال ایجاد پروژه...";


        try {

            // ------------------------------------------------
            // Send request to FastAPI
            // ------------------------------------------------

            const response =
                await fetch(
                    `/teacher/create-project?project_id=${encodeURIComponent(projectId)}`,
                    {
                        method: "POST",
                        body: formData
                    }
                );


            // ------------------------------------------------
            // Read response
            // ------------------------------------------------

            const data =
                await response.json();


            // ------------------------------------------------
            // Handle API error
            // ------------------------------------------------

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "ایجاد پروژه با خطا مواجه شد."
                );
            }


            // =================================================
            // SUCCESS
            // =================================================

            resultProjectId.textContent =
                data.project_id || projectId;


            resultFileName.textContent =
                data.filename || file.name;


            successResult.classList.remove(
                "hidden"
            );


            // Scroll to result

            setTimeout(
                () => {

                    successResult.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                },
                100
            );


            // Clear form

            form.reset();


        }
        catch (error) {

            console.error(
                "Teacher Project Error:",
                error
            );


            alert(
                "خطا در ایجاد پروژه:\n\n" +
                error.message
            );

        }
        finally {

            // ------------------------------------------------
            // Hide loading
            // ------------------------------------------------

            loading.classList.add(
                "hidden"
            );


            // ------------------------------------------------
            // Enable button
            // ------------------------------------------------

            createButton.disabled = false;

            createButton.textContent =
                "ایجاد و ذخیره پروژه";

        }

    }
);

