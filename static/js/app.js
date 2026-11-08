"use strict";

/**
 * Клиентская логика приложения «Контур».
 * Работает с REST API через Fetch API и обновляет интерфейс без перезагрузки.
 */
(() => {
    const API_URL = "/api/requests";
    const STATUSES = ["Новая", "В работе", "Выполнена", "Закрыта"];
    const STATUS_CLASSES = {
        "Новая": "badge-new",
        "В работе": "badge-progress",
        "Выполнена": "badge-done",
        "Закрыта": "badge-closed",
    };
    const PRIORITY_CLASSES = {
        "Низкий": "priority-low",
        "Средний": "priority-medium",
        "Высокий": "priority-high",
    };

    const state = {
        requests: [],
        filters: {
            status: "",
            category: "",
        },
    };

    const elements = {};
    let loadSequence = 0;

    /**
     * Возвращает ссылки на элементы страницы.
     */
    function cacheElements() {
        elements.createForm = document.getElementById("create-form");
        elements.createTitle = document.getElementById("create-title-input");
        elements.createDescription = document.getElementById("create-description");
        elements.createCategory = document.getElementById("create-category");
        elements.createPriority = document.getElementById("create-priority");
        elements.createSubmit = document.getElementById("create-submit");

        elements.filterStatus = document.getElementById("filter-status");
        elements.filterCategory = document.getElementById("filter-category");
        elements.resetFilters = document.getElementById("reset-filters");
        elements.refreshButton = document.getElementById("refresh-button");

        elements.requestsList = document.getElementById("requests-list");
        elements.loadingState = document.getElementById("loading-state");
        elements.emptyState = document.getElementById("empty-state");
        elements.emptyMessage = document.getElementById("empty-message");
        elements.requestCount = document.getElementById("request-count");

        elements.statTotal = document.getElementById("stat-total");
        elements.statNew = document.getElementById("stat-new");
        elements.statProgress = document.getElementById("stat-progress");
        elements.statDone = document.getElementById("stat-done");

        elements.editDialog = document.getElementById("edit-dialog");
        elements.editForm = document.getElementById("edit-form");
        elements.editId = document.getElementById("edit-id");
        elements.editTitle = document.getElementById("edit-title");
        elements.editDescription = document.getElementById("edit-description");
        elements.editCategory = document.getElementById("edit-category");
        elements.editPriority = document.getElementById("edit-priority");
        elements.editSubmit = document.getElementById("edit-submit");
        elements.editCancel = document.getElementById("edit-cancel");
        elements.editCancelIcon = document.getElementById("edit-cancel-icon");

        elements.toastContainer = document.getElementById("toast-container");
    }

    /**
     * Подключает обработчики событий интерфейса.
     */
    function bindEvents() {
        elements.createForm.addEventListener("submit", handleCreateRequest);
        elements.requestsList.addEventListener("click", handleListClick);
        elements.requestsList.addEventListener("change", handleStatusChange);
        elements.filterStatus.addEventListener("change", handleFilterChange);
        elements.filterCategory.addEventListener("change", handleFilterChange);
        elements.resetFilters.addEventListener("click", handleResetFilters);
        elements.refreshButton.addEventListener("click", () => loadRequests({ notify: true }));

        elements.editForm.addEventListener("submit", handleEditSubmit);
        elements.editCancel.addEventListener("click", closeEditDialog);
        elements.editCancelIcon.addEventListener("click", closeEditDialog);
        elements.editDialog.addEventListener("click", (event) => {
            if (event.target === elements.editDialog) {
                closeEditDialog();
            }
        });
    }

    /**
     * Выполняет HTTP-запрос к API и разбирает JSON-ответ.
     *
     * @param {string} url адрес запроса;
     * @param {object} options настройки fetch;
     * @returns {Promise<*>} данные ответа;
     */
    async function apiRequest(url, options = {}) {
        const requestOptions = {
            ...options,
            headers: {
                Accept: "application/json",
                ...(options.headers || {}),
            },
        };

        if (requestOptions.body) {
            requestOptions.headers["Content-Type"] = "application/json";
        }

        let response;
        try {
            response = await fetch(url, requestOptions);
        } catch (error) {
            throw new Error(
                "Не удалось соединиться с сервером. "
                + "Проверьте, что приложение запущено."
            );
        }

        const responseText = await response.text();
        let data = null;

        if (responseText) {
            try {
                data = JSON.parse(responseText);
            } catch (error) {
                throw new Error("Сервер вернул ответ в неожиданном формате.");
            }
        }

        if (!response.ok) {
            const message = data && data.error
                ? data.error
                : `Ошибка запроса (HTTP ${response.status}).`;
            throw new Error(message);
        }

        return data;
    }

    /**
     * Загружает заявки с учётом выбранных фильтров.
     *
     * @param {object} options дополнительные параметры;
     * @param {boolean} options.notify показывать уведомление об обновлении.
     */
    async function loadRequests(options = {}) {
        const sequence = ++loadSequence;
        setLoading(true);

        try {
            const params = new URLSearchParams();
            if (state.filters.status) {
                params.set("status", state.filters.status);
            }
            if (state.filters.category) {
                params.set("category", state.filters.category);
            }

            const query = params.toString();
            const url = query ? `${API_URL}?${query}` : API_URL;
            const requests = await apiRequest(url);

            if (sequence !== loadSequence) {
                return;
            }

            if (!Array.isArray(requests)) {
                throw new Error("Сервер вернул неожиданный формат списка заявок.");
            }

            state.requests = requests;
            renderRequests(requests);
            updateStats(requests);

            if (options.notify) {
                showToast(
                    `Список обновлён. Найдено заявок: ${requests.length}.`,
                    "info"
                );
            }
        } catch (error) {
            if (sequence !== loadSequence) {
                return;
            }

            state.requests = [];
            renderRequests([]);
            elements.emptyMessage.textContent =
                `Не удалось загрузить заявки. ${error.message}`;
            elements.emptyState.hidden = false;
            elements.requestCount.textContent = "0";
            updateStats([]);
            showToast(error.message, "error");
        } finally {
            if (sequence === loadSequence) {
                setLoading(false);
            }
        }
    }

    /**
     * Показывает или скрывает индикатор загрузки.
     *
     * @param {boolean} isLoading состояние загрузки.
     */
    function setLoading(isLoading) {
        elements.loadingState.hidden = !isLoading;
        elements.requestsList.hidden = isLoading;
        if (isLoading) {
            elements.emptyState.hidden = true;
        }
    }

    /**
     * Перерисовывает список заявок.
     *
     * @param {Array<object>} requests заявки для отображения.
     */
    function renderRequests(requests) {
        if (!requests.length) {
            elements.requestsList.innerHTML = "";
            const hasFilters = state.filters.status || state.filters.category;
            elements.emptyMessage.textContent = hasFilters
                ? "По выбранным фильтрам заявок не найдено. Измените условия поиска."
                : "Заявок пока нет. Создайте первую заявку в форме слева.";
            elements.emptyState.hidden = false;
            return;
        }

        elements.emptyState.hidden = true;
        elements.requestsList.hidden = false;
        elements.requestsList.innerHTML = requests
            .map(renderRequestCard)
            .join("");
    }

    /**
     * Формирует HTML-разметку одной карточки заявки.
     *
     * @param {object} request данные заявки;
     * @returns {string} HTML-разметка.
     */
    function renderRequestCard(request) {
        const statusClass = STATUS_CLASSES[request.status] || "badge-closed";
        const priorityClass = PRIORITY_CLASSES[request.priority] || "";
        const description = request.description
            ? escapeHtml(request.description)
            : "Описание не указано";
        const descriptionClass = request.description
            ? "request-description"
            : "request-description is-empty";

        return `
            <article class="request-card ${priorityClass}" data-id="${Number(request.id)}">
                <div class="request-top">
                    <span class="request-id">Заявка №${Number(request.id)}</span>
                    <span class="badge ${statusClass}">${escapeHtml(request.status)}</span>
                </div>

                <h4 class="request-title">${escapeHtml(request.title)}</h4>
                <p class="${descriptionClass}">${description}</p>

                <div class="request-meta">
                    <span class="badge badge-priority ${priorityClass}">
                        ${escapeHtml(request.priority)}
                    </span>
                    <span class="request-category">${escapeHtml(request.category)}</span>
                    <time class="request-date" datetime="${escapeHtml(request.created_at)}">
                        ${formatDate(request.created_at)}
                    </time>
                </div>

                <div class="request-actions">
                    <label class="status-control">
                        Статус
                        <select class="status-select" data-id="${Number(request.id)}">
                            ${statusOptions(request.status)}
                        </select>
                    </label>

                    <button
                        type="button"
                        class="button button-secondary"
                        data-action="edit"
                        data-id="${Number(request.id)}"
                    >
                        Редактировать
                    </button>

                    <button
                        type="button"
                        class="button button-danger"
                        data-action="delete"
                        data-id="${Number(request.id)}"
                    >
                        Удалить
                    </button>
                </div>
            </article>
        `;
    }

    /**
     * Создаёт список option для выбора статуса.
     *
     * @param {string} currentStatus текущий статус заявки;
     * @returns {string} HTML-разметка options.
     */
    function statusOptions(currentStatus) {
        return STATUSES.map((status) => {
            const selected = status === currentStatus ? " selected" : "";
            return `<option value="${status}"${selected}>${status}</option>`;
        }).join("");
    }

    /**
     * Обновляет карточки статистики по текущему списку.
     *
     * @param {Array<object>} requests заявки.
     */
    function updateStats(requests) {
        const total = requests.length;
        const newCount = requests.filter((item) => item.status === "Новая").length;
        const progressCount = requests.filter(
            (item) => item.status === "В работе"
        ).length;
        const doneCount = requests.filter(
            (item) => item.status === "Выполнена" || item.status === "Закрыта"
        ).length;

        elements.statTotal.textContent = String(total);
        elements.statNew.textContent = String(newCount);
        elements.statProgress.textContent = String(progressCount);
        elements.statDone.textContent = String(doneCount);
        elements.requestCount.textContent = String(total);
    }

    /**
     * Обрабатывает отправку формы создания заявки.
     *
     * @param {SubmitEvent} event событие отправки формы.
     */
    async function handleCreateRequest(event) {
        event.preventDefault();

        const payload = {
            title: elements.createTitle.value.trim(),
            description: elements.createDescription.value.trim(),
            category: elements.createCategory.value,
            priority: elements.createPriority.value,
        };

        if (!payload.title) {
            showToast("Введите название заявки.", "error");
            elements.createTitle.focus();
            return;
        }

        if (!payload.category) {
            showToast("Выберите категорию заявки.", "error");
            elements.createCategory.focus();
            return;
        }

        setButtonBusy(elements.createSubmit, true, "Создание…");

        try {
            const created = await apiRequest(API_URL, {
                method: "POST",
                body: JSON.stringify(payload),
            });
            elements.createForm.reset();
            showToast(`Заявка №${created.id} успешно создана.`, "success");
            await loadRequests();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setButtonBusy(elements.createSubmit, false);
        }
    }

    /**
     * Обрабатывает клики по кнопкам в списке заявок.
     *
     * @param {MouseEvent} event событие клика.
     */
    function handleListClick(event) {
        const button = event.target.closest("button[data-action]");
        if (!button) {
            return;
        }

        const requestId = Number(button.dataset.id);
        if (button.dataset.action === "edit") {
            openEditDialog(requestId);
        } else if (button.dataset.action === "delete") {
            handleDeleteRequest(requestId);
        }
    }

    /**
     * Обрабатывает изменение статуса в карточке заявки.
     *
     * @param {Event} event событие изменения select.
     */
    async function handleStatusChange(event) {
        const select = event.target.closest(".status-select");
        if (!select) {
            return;
        }

        const requestId = Number(select.dataset.id);
        const newStatus = select.value;
        const request = state.requests.find((item) => item.id === requestId);

        if (request && request.status === newStatus) {
            return;
        }

        select.disabled = true;

        try {
            await apiRequest(`${API_URL}/${requestId}/status`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus }),
            });
            showToast(
                `Заявка №${requestId}: новый статус — «${newStatus}».`,
                "success"
            );
            await loadRequests();
        } catch (error) {
            showToast(error.message, "error");
            if (request && select.isConnected) {
                select.value = request.status;
            }
        } finally {
            if (select.isConnected) {
                select.disabled = false;
            }
        }
    }

    /**
     * Удаляет заявку после подтверждения пользователя.
     *
     * @param {number} requestId идентификатор заявки.
     */
    async function handleDeleteRequest(requestId) {
        const request = state.requests.find((item) => item.id === requestId);
        const description = request
            ? `заявку №${requestId} «${request.title}»`
            : `заявку №${requestId}`;

        const confirmed = window.confirm(
            `Удалить ${description}? Это действие нельзя отменить.`
        );

        if (!confirmed) {
            return;
        }

        try {
            await apiRequest(`${API_URL}/${requestId}`, { method: "DELETE" });
            showToast(`Заявка №${requestId} удалена.`, "success");
            await loadRequests();
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    /**
     * Открывает диалоговое окно редактирования заявки.
     *
     * @param {number} requestId идентификатор заявки.
     */
    async function openEditDialog(requestId) {
        try {
            const request = await apiRequest(`${API_URL}/${requestId}`);
            elements.editId.value = String(request.id);
            elements.editTitle.value = request.title;
            elements.editDescription.value = request.description;
            elements.editCategory.value = request.category;
            elements.editPriority.value = request.priority;

            if (typeof elements.editDialog.showModal === "function") {
                elements.editDialog.showModal();
            } else {
                elements.editDialog.setAttribute("open", "");
            }

            elements.editTitle.focus();
        } catch (error) {
            showToast(error.message, "error");
        }
    }

    /**
     * Закрывает диалоговое окно редактирования.
     */
    function closeEditDialog() {
        if (typeof elements.editDialog.close === "function") {
            elements.editDialog.close();
        } else {
            elements.editDialog.removeAttribute("open");
        }
    }

    /**
     * Сохраняет изменения заявки через PUT-запрос.
     *
     * @param {SubmitEvent} event событие отправки формы редактирования.
     */
    async function handleEditSubmit(event) {
        event.preventDefault();

        const requestId = Number(elements.editId.value);
        const payload = {
            title: elements.editTitle.value.trim(),
            description: elements.editDescription.value.trim(),
            category: elements.editCategory.value,
            priority: elements.editPriority.value,
        };

        if (!payload.title) {
            showToast("Название заявки не может быть пустым.", "error");
            elements.editTitle.focus();
            return;
        }

        if (!payload.category) {
            showToast("Выберите категорию заявки.", "error");
            elements.editCategory.focus();
            return;
        }

        setButtonBusy(elements.editSubmit, true, "Сохранение…");

        try {
            await apiRequest(`${API_URL}/${requestId}`, {
                method: "PUT",
                body: JSON.stringify(payload),
            });
            closeEditDialog();
            showToast(`Заявка №${requestId} обновлена.`, "success");
            await loadRequests();
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            setButtonBusy(elements.editSubmit, false);
        }
    }

    /**
     * Применяет выбранные фильтры.
     */
    function handleFilterChange() {
        state.filters.status = elements.filterStatus.value;
        state.filters.category = elements.filterCategory.value;
        loadRequests();
    }

    /**
     * Сбрасывает фильтры и перезагружает список.
     */
    function handleResetFilters() {
        elements.filterStatus.value = "";
        elements.filterCategory.value = "";
        state.filters.status = "";
        state.filters.category = "";
        loadRequests();
        showToast("Фильтры сброшены.", "info");
    }

    /**
     * Меняет текст и состояние кнопки во время запроса.
     *
     * @param {HTMLButtonElement} button кнопка;
     * @param {boolean} isBusy признак выполнения запроса;
     * @param {string} busyText текст на время запроса.
     */
    function setButtonBusy(button, isBusy, busyText = "Подождите…") {
        if (isBusy) {
            button.dataset.originalText = button.textContent;
            button.textContent = busyText;
            button.disabled = true;
            return;
        }

        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }

    /**
     * Показывает всплывающее уведомление.
     *
     * @param {string} message текст сообщения;
     * @param {string} type тип: success, error или info.
     */
    function showToast(message, type = "info") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        elements.toastContainer.appendChild(toast);

        window.setTimeout(() => {
            toast.classList.add("toast-leaving");
            window.setTimeout(() => toast.remove(), 250);
        }, 3600);
    }

    /**
     * Экранирует HTML-спецсимволы перед вставкой в разметку.
     *
     * @param {*} value значение;
     * @returns {string} безопасная строка.
     */
    function escapeHtml(value) {
        const replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        };

        return String(value ?? "").replace(
            /[&<>"']/g,
            (character) => replacements[character]
        );
    }

    /**
     * Форматирует дату для отображения на русском языке.
     *
     * @param {string} value строка даты с сервера;
     * @returns {string} отформатированная дата.
     */
    function formatDate(value) {
        if (!value) {
            return "дата не указана";
        }

        const date = new Date(String(value).replace(" ", "T"));
        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return new Intl.DateTimeFormat("ru-RU", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(date);
    }

    /**
     * Точка входа клиентского приложения.
     */
    function init() {
        cacheElements();
        bindEvents();
        loadRequests();
    }

    document.addEventListener("DOMContentLoaded", init);
})();
