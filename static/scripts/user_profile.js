// for editing teacher's bio
function editBioNow() {
    document.getElementById("originalTextarea").setAttribute("hidden", null);
    document.getElementById("editedTextarea").removeAttribute("hidden");
}
function cancelBio() {
    document.getElementById("originalTextarea").removeAttribute("hidden");
    document.getElementById("editedTextarea").setAttribute("hidden", null);
}

$(document).ready(function(){
    $("#editProfileButton").click(function(){
        $("#imageForm").toggle();
    });
});

// Dropzone.js for segmenting data payload to chunks of data
Dropzone.options.dropper = {
    maxFiles: 1,
    paramName: 'profileImage',
    acceptedFiles: ".jpeg,.jpg,.png",
    chunking: true,
    forceChunking: true,
    url: '/user_profile',
    maxFilesize: 50, // megabytes
    chunkSize: 1000000, // bytes
    retryChunks: true,
    retryChunksLimit: 3,
    autoProcessQueue: false,
    init: function() {
        let myDropzone = this;
        
        myDropzone.on("addedfile", function() {
            $(".dz-progress").hide();
            if (myDropzone.files[1] == null) return;
            myDropzone.removeFile(myDropzone.files[0]);
        });

        document.getElementById('submit-button').addEventListener("click", function (e) {
            e.preventDefault();
            myDropzone.processQueue();
        });

        myDropzone.on("success", function () {
            function redirectUser() {
                location.reload();
            }
            setInterval(redirectUser, 1500);
        });

        myDropzone.on('sending', function(file, xhr, formData) {
            /* Append inputs to FormData */
            $(".dz-progress").show();
            formData.append("imageProfile", document.getElementById('dropper').value);
        });
    }
};