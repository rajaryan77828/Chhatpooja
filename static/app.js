
// ================================================
// CHHATH.PARV - MAIN JAVASCRIPT
// Frontend + Flask Wishes API
// ================================================

"use strict";

// ================================================
// CONFIGURATION
// ================================================

// Same Flask server on VS Code forwarded port 5000.
const API_BASE = "";

// Estimated Patna sunset on Chhath evening.
// Update if you have a verified local timing.
const CHHATH_TARGET = "2026-11-15T17:01:00+05:30";


// ================================================
// DOM ELEMENTS
// ================================================

const wishForm = document.getElementById("wishForm");
const wishWall = document.getElementById("wishWall");
const formStatus = document.getElementById("formStatus");

const submitButton = wishForm
    ? wishForm.querySelector('button[type="submit"]')
    : null;

const messageInput = document.getElementById("message");
const charCount = document.getElementById("charCount");


// ================================================
// SAFE TEXT
// ================================================

function safeText(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
}


// ================================================
// COUNTDOWN
// ================================================

function updateCountdown() {
    const countdown = document.getElementById("countdown");

    if (!countdown) return;

    const target = new Date(CHHATH_TARGET).getTime();
    const now = Date.now();
    const difference = target - now;

    if (difference <= 0) {
        countdown.innerHTML = `
            <div class="countdown-finished">
                शुभ छठ महापर्व! 🙏
            </div>
        `;
        return;
    }

    const days = Math.floor(difference / (1000 * 60 * 60 * 24));
    const hours = Math.floor(
        (difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
    );
    const minutes = Math.floor(
        (difference % (1000 * 60 * 60)) / (1000 * 60)
    );
    const seconds = Math.floor(
        (difference % (1000 * 60)) / 1000
    );

    const units = [
        { label: "Days", value: days },
        { label: "Hours", value: hours },
        { label: "Minutes", value: minutes },
        { label: "Seconds", value: seconds }
    ];

    countdown.innerHTML = units.map(unit => `
        <div class="countdown-item">
            <span class="countdown-number">
                ${String(unit.value).padStart(2, "0")}
            </span>
            <span class="countdown-label">
                ${unit.label}
            </span>
        </div>
    `).join("");
}


// ================================================
// WISH DATE FORMAT
// ================================================

function formatWishDate(dateString) {
    if (!dateString) return "";

    const date = new Date(dateString);

    if (Number.isNaN(date.getTime())) return "";

    return date.toLocaleDateString("hi-IN", {
        day: "numeric",
        month: "short",
        year: "numeric"
    });
}


// ================================================
// LOAD WISHES FROM FLASK API
// ================================================

async function loadWishes() {
    if (!wishWall) return;

    try {
        const response = await fetch(`${API_BASE}/api/wishes`, {
            method: "GET",
            headers: {
                "Accept": "application/json"
            }
        });

        const contentType =
            response.headers.get("content-type") || "";

        if (!contentType.includes("application/json")) {
            throw new Error(
                "The server returned HTML instead of JSON. Check your Flask port 5000."
            );
        }

        const wishes = await response.json();

        if (!response.ok) {
            throw new Error(
                wishes.error || "Unable to load wishes."
            );
        }

        renderWishes(wishes);

    } catch (error) {
        console.error("Load wishes error:", error);

        wishWall.innerHTML = `
            <p class="empty-state">
                ${safeText(error.message)}
            </p>
        `;
    }
}


// ================================================
// RENDER WISHES
// ================================================

function renderWishes(wishes) {
    if (!wishWall) return;

    if (!Array.isArray(wishes) || wishes.length === 0) {
        wishWall.innerHTML = `
            <p class="empty-state">
                अभी तक कोई शुभकामना नहीं आई है।
                पहली शुभकामना आप साझा करें! 🙏
            </p>
        `;
        return;
    }

    wishWall.innerHTML = wishes.map(wish => `
        <article class="wish-card">

            <div class="wish-card-header">

                <span class="wish-author">
                    ${safeText(wish.name)}
                </span>

                <span class="wish-date">
                    ${safeText(formatWishDate(wish.created_at))}
                </span>

            </div>

            <p class="wish-message">
                ${safeText(wish.message)}
            </p>

        </article>
    `).join("");
}


// ================================================
// SUBMIT WISH TO FLASK API
// ================================================

if (wishForm) {

    wishForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const nameInput = document.getElementById("name");

        const name = nameInput
            ? nameInput.value.trim()
            : "";

        const message = messageInput
            ? messageInput.value.trim()
            : "";

        if (!name || !message) {
            if (formStatus) {
                formStatus.textContent =
                    "कृपया अपना नाम और शुभकामना लिखें।";
            }
            return;
        }

        if (name.length > 40) {
            formStatus.textContent =
                "नाम 40 अक्षरों से अधिक नहीं होना चाहिए।";
            return;
        }

        if (message.length > 240) {
            formStatus.textContent =
                "शुभकामना 240 अक्षरों से अधिक नहीं होनी चाहिए।";
            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Sharing...";
        }

        if (formStatus) {
            formStatus.textContent = "";
        }

        try {

            const response = await fetch(
                `${API_BASE}/api/wishes`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },

                    body: JSON.stringify({
                        name: name,
                        message: message
                    })
                }
            );

            const contentType =
                response.headers.get("content-type") || "";

            if (!contentType.includes("application/json")) {
                throw new Error(
                    "HTML response received. Your request is not reaching the Flask API."
                );
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to share your wish."
                );
            }

            if (formStatus) {
                formStatus.textContent = result.message;
            }

            wishForm.reset();

            if (charCount) {
                charCount.textContent = "0";
            }

            // Refresh the community wish wall.
            await loadWishes();

        } catch (error) {

            console.error("Submit wish error:", error);

            if (formStatus) {
                formStatus.textContent = error.message;
            }

        } finally {

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Share my wish ↗";
            }

        }

    });

}


// ================================================
// CHARACTER COUNTER
// ================================================

if (messageInput && charCount) {

    function updateCharacterCount() {
        charCount.textContent = messageInput.value.length;
    }

    messageInput.addEventListener(
        "input",
        updateCharacterCount
    );

    updateCharacterCount();

}


// ================================================
// SHARE WEBSITE
// ================================================

async function shareWebsite() {

    const shareData = {
        title: "CHHATH.PARV",
        text: "छठ महापर्व की हार्दिक शुभकामनाएं! जय छठी मईया 🙏",
        url: window.location.href
    };

    try {

        if (navigator.share) {

            await navigator.share(shareData);

        } else if (navigator.clipboard) {

            await navigator.clipboard.writeText(
                window.location.href
            );

            alert("Website link copied successfully!");

        } else {

            prompt("Copy this website link:", window.location.href);

        }

    } catch (error) {

        if (error.name !== "AbortError") {
            console.error("Sharing error:", error);
        }

    }

}


// ================================================
// SHARE BUTTON EVENT
// ================================================

document.querySelectorAll("[data-share]").forEach(button => {

    button.addEventListener("click", shareWebsite);

});


// ================================================
// MOBILE NAVIGATION
// ================================================

const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector(".nav-links");

if (menuButton && navigation) {

    menuButton.addEventListener("click", () => {

        const isOpen = navigation.classList.toggle("active");

        menuButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );

    });

    navigation.querySelectorAll("a").forEach(link => {

        link.addEventListener("click", () => {

            navigation.classList.remove("active");

            menuButton.setAttribute(
                "aria-expanded",
                "false"
            );

        });

    });

}


// ================================================
// SMOOTH SCROLL
// ================================================

document.querySelectorAll('a[href^="#"]').forEach(link => {

    link.addEventListener("click", function (event) {

        const targetId = this.getAttribute("href");

        if (!targetId || targetId === "#") return;

        const target = document.querySelector(targetId);

        if (target) {

            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }

    });

});


// ================================================
// INITIALIZE WEBSITE
// ================================================

function initializeWebsite() {

    updateCountdown();

    loadWishes();

}

// Initialize once, whether script loads in head or at end of body.
if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initializeWebsite,
        { once: true }
    );

} else {

    initializeWebsite();

}

// Refresh countdown every second.
setInterval(updateCountdown, 1000);
