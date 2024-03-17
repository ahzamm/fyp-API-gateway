const dropZone = document.querySelector("#drop-zone");

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("dragover");
  const files = e.dataTransfer.files;
  handleImageUpload(files[0]);
});

dropZone.addEventListener("click", () => {
  const fileInput = document.createElement("input");
  fileInput.type = "file";
  fileInput.accept = ".jpg";
  fileInput.addEventListener("change", () =>
    handleImageUpload(fileInput.files[0])
  );
  fileInput.click();
});

function handleImageUpload(file) {
  if (file.type !== "image/jpeg") {
    alert("Only .jpg images are allowed!");
    return;
  }

  // Show the loading animation
  document.getElementById("loading").style.display = "block";

  const img = document.createElement("img");
  img.src = URL.createObjectURL(file);
  img.onload = () => URL.revokeObjectURL(img.src);
  dropZone.innerHTML = "";
  dropZone.append(img);

  var formData = new FormData();
  formData.append("image", file);

  fetch("/home", {
    method: "POST",
    body: formData,
  }).then((response) => {
    // Hide the loading animation
    document.getElementById("loading").style.display = "none";
    location.reload();
  });
}
