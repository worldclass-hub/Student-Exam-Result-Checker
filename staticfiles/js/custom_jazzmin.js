// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
    // Check if we are on the login page
    const loginContainer = document.querySelector(".login-box");

    if (loginContainer) {
        // Inject the video into the body
        const video = document.createElement("video");
        video.autoplay = true;
        video.muted = true;
        video.loop = true;
        video.id = "background-video";

        // Check screen size and load different video
        const videoSource = document.createElement("source");
        if (window.innerWidth < 768) {
            // Mobile view: small screen (video for mobile)
            videoSource.src = "/static/videos/People Working in Office - Busy Day - Royalty Free Stock Video.mp4";  // Mobile video path
        } else {
            // Large screen: bigger screen (video for larger devices)
            videoSource.src = "/static/videos/Business Man Walking(1080p).mp4";  // Desktop video path
        }

        videoSource.type = "video/mp4";

        // Append the source to the video
        video.appendChild(videoSource);

        // Style the video
        video.style.position = "fixed";
        video.style.top = "0";
        video.style.left = "0";
        video.style.width = "100vw";
        video.style.height = "100vh";
        video.style.objectFit = "cover";
        video.style.zIndex = "-1";

        // Inject the video into the body
        document.body.prepend(video);
    }
});



document.addEventListener("DOMContentLoaded", function () {
    const avatarUrl = document.querySelector("#user-tools img"); // Check for existing user image

    if (!avatarUrl) {
        // Default to a placeholder if the avatar isn't found
        const avatarContainer = document.querySelector("#user-tools");
        if (avatarContainer) {
            const avatarImage = document.createElement("img");
            avatarImage.src = "/static/img/doxcela2.png"; // Replace with your default avatar path
            avatarImage.alt = "User Avatar";
            avatarImage.style.width = "30px";
            avatarImage.style.height = "30px";
            avatarImage.style.borderRadius = "50%";
            avatarImage.style.marginRight = "10px";
            avatarContainer.prepend(avatarImage);
        }
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const userAvatar = document.querySelector(".user-avatar"); // Adjust selector if needed
    if (userAvatar && userAvatar.dataset.avatarUrl) {
        userAvatar.src = userAvatar.dataset.avatarUrl;
    }
});
