document.addEventListener("DOMContentLoaded", () => {
    console.log("main.js loaded");
    // ▼ プロフィールドロップダウン
    const dropdown = document.querySelector("[data-dropdown]");
    if (dropdown) {
        const toggleBtn = dropdown.querySelector(".icon-user");
        const panel = dropdown.querySelector(".dropdown-panel");

        if (toggleBtn && panel) {
        // アイコン押したら開閉
        toggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("open");
        });

        // パネル内クリックは閉じない
        panel.addEventListener("click", (e) => {
            e.stopPropagation();
        });

        // それ以外をクリックしたら閉じる
        document.addEventListener("click", () => {
            dropdown.classList.remove("open");
        });
        }
    }

    // ▼ ログアウトモーダル
    const logoutTrigger = document.querySelector("[data-logout-trigger]");
    const logoutModal = document.querySelector("[data-logout-modal]");
    const logoutConfirm = document.querySelector("[data-logout-confirm]");
    const logoutCancel = document.querySelector("[data-logout-cancel]");
    const logoutBackdrop = document.querySelector("[data-logout-dismiss]");

    if (logoutTrigger && logoutModal && logoutConfirm) {
        const logoutUrl = logoutTrigger.dataset.logoutUrl;

        const openModal = () => {
        logoutModal.hidden = false;
        logoutConfirm.dataset.logoutUrl = logoutUrl;
        };

        const closeModal = () => {
        logoutModal.hidden = true;
        };

        logoutTrigger.addEventListener("click", openModal);

        if (logoutCancel) {
        logoutCancel.addEventListener("click", closeModal);
        }
        if (logoutBackdrop) {
        logoutBackdrop.addEventListener("click", closeModal);
        }

        logoutConfirm.addEventListener("click", () => {
        const url = logoutConfirm.dataset.logoutUrl;
        if (url) {
            window.location.href = url;
        }
        });
    }
});