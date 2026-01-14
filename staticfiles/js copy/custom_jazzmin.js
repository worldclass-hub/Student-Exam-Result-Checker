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
