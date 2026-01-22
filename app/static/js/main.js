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
    const hasLogoutModal = Boolean(logoutModal && logoutConfirm);

    if (logoutTrigger) {
        const resolveLogoutUrl = () =>
        logoutTrigger.dataset.logoutUrl || logoutTrigger.getAttribute("href");

        const openModal = () => {
        if (!logoutModal) {
            return;
        }
        console.log("open logout modal");
        logoutModal.removeAttribute("hidden");
        logoutModal.classList.add("is-open");
        dropdown?.classList.remove("open");
        };

        const closeModal = () => {
        if (!logoutModal) {
            return;
        }
        logoutModal.classList.remove("is-open");
        logoutModal.setAttribute("hidden", "");
        };

        logoutTrigger.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!hasLogoutModal) {
            const url = resolveLogoutUrl();
            if (url) {
            window.location.href = url;
            }
            return;
        }
        openModal();
        });

        if (hasLogoutModal) {
        if (logoutCancel) {
            logoutCancel.addEventListener("click", closeModal);
        }
        if (logoutBackdrop) {
            logoutBackdrop.addEventListener("click", closeModal);
        }

        logoutConfirm.addEventListener("click", () => {
            const url = logoutConfirm.dataset.logoutUrl || resolveLogoutUrl();
            if (url) {
            window.location.href = url;
            }
        });
        }
    }

    // ▼ プラン削除確認
    const deleteModal = document.querySelector("[data-plan-delete-modal]");
    const deleteMessage = deleteModal?.querySelector("[data-plan-delete-message]");
    const deleteConfirm = deleteModal?.querySelector("[data-plan-delete-confirm]");
    const deleteCancel = deleteModal?.querySelector("[data-plan-delete-cancel]");
    const deleteBackdrop = deleteModal?.querySelector("[data-plan-delete-dismiss]");
    let pendingDeleteForm = null;

    const openDeleteModal = (title) => {
        if (!deleteModal) {
        return false;
        }
        const message = title
        ? `「${title}」を削除しますか？`
        : "このプランを削除しますか？";
        if (deleteMessage) {
        deleteMessage.textContent = message;
        deleteMessage.hidden = false;
        }
        deleteModal.hidden = false;
        deleteModal.classList.add("is-open");
        return true;
    };

    const closeDeleteModal = () => {
        if (!deleteModal) {
        return;
        }
        deleteModal.classList.remove("is-open");
        deleteModal.hidden = true;
        if (deleteMessage) {
        deleteMessage.textContent = "";
        deleteMessage.hidden = true;
        }
        pendingDeleteForm = null;
    };

    document.querySelectorAll("[data-plan-delete]").forEach((form) => {
        form.addEventListener("submit", (event) => {
        const title = form.getAttribute("data-plan-title");
        if (!openDeleteModal(title)) {
            const message = title
            ? `「${title}」を削除しますか？`
            : "このプランを削除しますか？";
            if (!window.confirm(message)) {
            event.preventDefault();
            }
            return;
        }
        event.preventDefault();
        pendingDeleteForm = form;
        });
    });

    deleteConfirm?.addEventListener("click", () => {
        if (pendingDeleteForm) {
        pendingDeleteForm.submit();
        }
        closeDeleteModal();
    });

    deleteCancel?.addEventListener("click", closeDeleteModal);
    deleteBackdrop?.addEventListener("click", closeDeleteModal);
});
