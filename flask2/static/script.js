function toggleMenu() {
    var menuList = document.getElementById("menuList");
    menuList.classList.toggle("show");
  }
  
  // Image preview function
  document.getElementById("fileInput").addEventListener("change", function() {
    var preview = document.getElementById("imagePreview");
    var file = this.files[0];
    var reader = new FileReader();
  
    reader.onloadend = function() {
      preview.src = reader.result;
    }
  
    if (file) {
      reader.readAsDataURL(file);
    } else {
      preview.src = "";
    }
  });
  