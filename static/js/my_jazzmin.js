// ✅ Background video on login page
document.addEventListener("DOMContentLoaded", function () {
    const loginContainer = document.querySelector(".login-box");
    if (loginContainer) {
        const video = document.createElement("video");
        video.autoplay = true;
        video.muted = true;
        video.loop = true;
        video.id = "background-video";

        const videoSource = document.createElement("source");
        videoSource.src =
            window.innerWidth < 768
                ? "/static/videos/Thank You Jesus - Hillsong Worship.mp4"
                : "/static/videos/Thank You Jesus - Hillsong Worship.mp4";
        videoSource.type = "video/mp4";

        video.appendChild(videoSource);
        document.body.prepend(video);
    }
});

// ✅ Avatar fallback
document.addEventListener("DOMContentLoaded", function () {
    const avatarUrl = document.querySelector("#user-tools img");
    if (!avatarUrl) {
        const avatarContainer = document.querySelector("#user-tools");
        if (avatarContainer) {
            const avatarImage = document.createElement("img");
            avatarImage.src = "/static/login-form/images/GMMI_LOGO.png";
            avatarImage.alt = "User Avatar";
            avatarImage.style.width = "30px";
            avatarImage.style.height = "30px";
            avatarImage.style.borderRadius = "50%";
            avatarImage.style.marginRight = "10px";
            avatarContainer.prepend(avatarImage);
        }
    }
});

// ✅ Avatar from data-avatar-url
document.addEventListener("DOMContentLoaded", function () {
    const userAvatar = document.querySelector(".user-avatar");
    if (userAvatar && userAvatar.dataset.avatarUrl) {
        userAvatar.src = userAvatar.dataset.avatarUrl;
    }
});

// ✅ Inject floating Home button (not on login page)
document.addEventListener("DOMContentLoaded", function () {
    const loginContainer = document.querySelector(".login-box");
    if (!loginContainer) {
        const homeButton = document.createElement("a");
        homeButton.href = "/";
        homeButton.className = "floating-home-btn";
        homeButton.title = "Go to Home";
        homeButton.innerHTML = `<i class="fas fa-home"></i>`;
        document.body.appendChild(homeButton);
    }
});

// ✅ Scroll-based hide/show for floating Home button
document.addEventListener("DOMContentLoaded", function () {
    let lastScrollTop = 0;
    const homeBtn = document.querySelector(".floating-home-btn");

    if (homeBtn) {
        window.addEventListener("scroll", function () {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            if (scrollTop > lastScrollTop) {
                // Scrolling down
                homeBtn.classList.add("hide");
            } else {
                // Scrolling up
                homeBtn.classList.remove("hide");
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        });
    }
});
