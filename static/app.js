const fileInput = document.getElementById("arquivo");
const fileName = document.getElementById("file-name");
const dropzone = document.getElementById("dropzone");
const form = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");

if (fileInput && fileName) {
    fileInput.addEventListener("change", () => {
        const hasFile = fileInput.files && fileInput.files.length > 0;
        fileName.textContent = hasFile ? fileInput.files[0].name : "Nenhum arquivo selecionado";
    });
}

if (dropzone && fileInput) {
    const activate = () => dropzone.classList.add("drag-active");
    const deactivate = () => dropzone.classList.remove("drag-active");

    dropzone.addEventListener("dragover", (event) => {
        event.preventDefault();
        activate();
    });

    dropzone.addEventListener("dragleave", () => {
        deactivate();
    });

    dropzone.addEventListener("drop", (event) => {
        event.preventDefault();
        deactivate();

        if (!event.dataTransfer || !event.dataTransfer.files.length) {
            return;
        }

        fileInput.files = event.dataTransfer.files;
        fileInput.dispatchEvent(new Event("change"));
    });
}

if (form && submitBtn) {
    form.addEventListener("submit", () => {
        submitBtn.classList.add("is-loading");
        submitBtn.disabled = true;
    });
}
