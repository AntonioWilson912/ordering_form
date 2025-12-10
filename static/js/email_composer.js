class EmailComposer {
  constructor() {
    this.isMinimized = false;
    this.orderData = null;
    this.hasDraft = false;
    this.hasUnsavedChanges = false;
    this.emailSent = false;
    this.templates = [];
    this.init();
  }

  init() {
    const composerHtml = `
      <div id="emailComposer" class="email-composer">
        <div class="email-header">
          <h4 id="emailHeaderTitle">
            <i class="fa-solid fa-envelope"></i>
            Compose Order Email
            <span class="draft-indicator" id="draftIndicator" style="display: none;">
              <i class="fa-solid fa-circle"></i> Draft saved
            </span>
          </h4>
          <div class="email-controls">
            <button id="minimizeEmail" type="button" title="Minimize">
              <i class="fa-solid fa-window-minimize"></i>
            </button>
            <button id="closeEmail" type="button" title="Close">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        </div>
        <div class="email-body">
          <form id="emailForm">
            <input type="hidden" id="orderId" name="order_id">

            <!-- Template Selector -->
            <div class="form-group template-selector">
              <label for="templateSelect">Template:</label>
              <select id="templateSelect" class="form-control">
                <option value="">-- Select Template --</option>
              </select>
              <small class="form-text">Choose a template or compose from scratch</small>
            </div>

            <div class="form-group">
              <label for="emailTo">To:</label>
              <input type="email" id="emailTo" name="to" class="form-control" required>
            </div>

            <div class="form-group sender-info">
              <label>From:</label>
              <div class="sender-display">
                <span id="senderName">Loading...</span>
                <small class="form-text">Replies will go to your email address</small>
              </div>
            </div>

            <div class="form-group">
              <label for="emailSubject">Subject:</label>
              <input type="text" id="emailSubject" name="subject" class="form-control" required>
            </div>

            <div class="form-group">
              <label for="emailContent">Message:</label>
              <textarea id="emailContent" name="content" class="form-control" required></textarea>
            </div>

            <div class="email-actions">
              <button type="button" class="btn btn-outline btn-sm" id="saveDraft">
                <i class="fa-solid fa-save"></i> Save Draft
              </button>
              <button type="submit" class="btn btn-blue btn-sm">
                <i class="fa-solid fa-paper-plane"></i> Send
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    $("body").append(composerHtml);
    this.bindEvents();
  }

  bindEvents() {
    const self = this;

    $("#emailHeaderTitle").click(function () {
      self.toggleMinimize();
    });

    $(".email-controls").click(function (e) {
      e.stopPropagation();
    });

    $("#closeEmail").click(function () {
      self.close();
    });

    $("#minimizeEmail").click(function () {
      self.toggleMinimize();
    });

    $("#saveDraft").click(function () {
      self.saveDraft();
    });

    $("#emailForm").submit(function (e) {
      e.preventDefault();
      self.sendEmail();
    });

    $("#emailTo, #emailSubject, #emailContent").on("input change", function () {
      self.hasUnsavedChanges = true;
      if (self.hasDraft) {
        $("#draftIndicator").hide();
        self.hasDraft = false;
      }
    });

    // Template selection
    $("#templateSelect").change(function () {
      const templateId = $(this).val();
      if (templateId) {
        self.applyTemplate(templateId);
      }
    });
  }

  async loadUserInfo() {
    try {
      const response = await $.ajax({
        url: "/api/user/email-info/",
        type: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (response.success) {
        $("#senderName").text(response.sender_name);
        this.userInfo = response;
        this.templates = response.templates || [];

        // Populate template selector
        this.populateTemplates();
      }
    } catch (error) {
      console.error("Failed to load user info:", error);
      $("#senderName").text("Order Form");
    }
  }

  populateTemplates() {
    const select = $("#templateSelect");
    select.find("option:not(:first)").remove();

    this.templates.forEach((t) => {
      const defaultLabel = t.is_default ? " (Default)" : "";
      select.append(
        `<option value="${t.id}"${t.is_default ? " selected" : ""}>${
          t.name
        }${defaultLabel}</option>`
      );
    });
  }

  async applyTemplate(templateId) {
    if (!this.orderData) return;

    try {
      const response = await $.ajax({
        url: "/api/email/render-template/",
        type: "POST",
        data: {
          template_id: templateId,
          order_id: this.orderData.order_id,
          csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
        },
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (response.success) {
        $("#emailSubject").val(response.subject);
        $("#emailContent").val(response.body);
        this.hasUnsavedChanges = true;
        this.showNotification("Template applied", "success");
      }
    } catch (error) {
      console.error("Failed to apply template:", error);
      this.showNotification("Failed to apply template", "error");
    }
  }

  async open(orderData, companyEmail) {
    this.orderData = orderData;
    this.hasUnsavedChanges = false;
    this.emailSent = false;

    await this.loadUserInfo();

    $("#orderId").val(orderData.order_id);

    const hasDraft = await this.loadDraft(orderData.order_id);

    if (!hasDraft) {
      $("#emailTo").val(companyEmail || "");

      // Check for default template
      const defaultTemplate = this.templates.find((t) => t.is_default);
      if (defaultTemplate) {
        await this.applyTemplate(defaultTemplate.id);
        this.hasUnsavedChanges = false;
      } else {
        // Render with no template (uses fallback)
        await this.renderDefaultContent();
      }

      this.hasDraft = false;
      $("#draftIndicator").hide();
    }

    $("#emailComposer").addClass("show").fadeIn(300);
  }

  async renderDefaultContent() {
    try {
      const response = await $.ajax({
        url: "/api/email/render-template/",
        type: "POST",
        data: {
          order_id: this.orderData.order_id,
          csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
        },
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (response.success) {
        $("#emailSubject").val(response.subject);
        $("#emailContent").val(response.body);
      }
    } catch (error) {
      // Fallback to basic template
      $("#emailSubject").val("Order Request");
      const content = this.generateBasicContent(this.orderData);
      $("#emailContent").val(content);
    }
  }

  generateBasicContent(orderData) {
    let content = "Hello,\n\nHere is my order:\n\n";

    orderData.items.forEach((item) => {
      const quantity = item.quantity;
      let unit;

      if (item.item_type === "C") {
        unit = quantity === 1 ? "case" : "cases";
      } else {
        unit = quantity === 1 ? "lb." : "lbs.";
      }

      const itemNo = item.item_no || "N/A";
      content += `${quantity} ${unit} - ${itemNo} ${item.product_name}\n`;
    });

    content += "\nThank you";
    return content;
  }

  async loadDraft(orderId) {
    try {
      const response = await $.ajax({
        url: `/api/orders/${orderId}/draft/`,
        type: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      if (response.success && response.draft) {
        $("#emailTo").val(response.draft.to);
        $("#emailSubject").val(response.draft.subject);
        $("#emailContent").val(response.draft.content);

        this.hasDraft = true;
        this.hasUnsavedChanges = false;
        $("#draftIndicator").show();

        this.showNotification("Draft loaded", "success");
        return true;
      }

      return false;
    } catch (error) {
      return false;
    }
  }

  toggleMinimize() {
    this.isMinimized = !this.isMinimized;
    $("#emailComposer").toggleClass("minimized");

    if (this.isMinimized) {
      $("#minimizeEmail i")
        .removeClass("fa-window-minimize")
        .addClass("fa-window-maximize");
    } else {
      $("#minimizeEmail i")
        .removeClass("fa-window-maximize")
        .addClass("fa-window-minimize");
    }
  }

  close() {
    if (this.hasUnsavedChanges && !this.emailSent && !this.hasDraft) {
      const hasContent =
        $("#emailContent").val().trim() !== "" ||
        $("#emailTo").val().trim() !== "";

      if (
        hasContent &&
        !confirm("Close without saving? Any unsaved changes will be lost.")
      ) {
        return;
      }
    }

    $("#emailComposer").removeClass("show").fadeOut(300);
    this.resetForm();
  }

  resetForm() {
    $("#emailForm")[0].reset();
    $("#templateSelect").val("");
    this.hasDraft = false;
    this.hasUnsavedChanges = false;
    this.emailSent = false;
    this.orderData = null;
    this.isMinimized = false;
    $("#draftIndicator").hide();
    $("#minimizeEmail i")
      .removeClass("fa-window-maximize")
      .addClass("fa-window-minimize");
  }

  saveDraft() {
    const formData = {
      order_id: $("#orderId").val(),
      to: $("#emailTo").val(),
      subject: $("#emailSubject").val(),
      content: $("#emailContent").val(),
      csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
    };

    $.ajax({
      url: "/api/orders/save-draft/",
      type: "POST",
      data: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
      success: (response) => {
        if (response.success) {
          this.hasDraft = true;
          this.hasUnsavedChanges = false;
          $("#draftIndicator").show();
          this.showNotification("Draft saved successfully!", "success");
        } else {
          this.showNotification(
            response.message || "Failed to save draft",
            "error"
          );
        }
      },
      error: (xhr) => {
        this.showNotification("Error saving draft", "error");
      },
    });
  }

  sendEmail() {
    const formData = {
      order_id: $("#orderId").val(),
      to: $("#emailTo").val(),
      subject: $("#emailSubject").val(),
      content: $("#emailContent").val(),
      csrfmiddlewaretoken: $("[name=csrfmiddlewaretoken]").val(),
    };

    $.ajax({
      url: "/api/orders/send-email/",
      type: "POST",
      data: formData,
      headers: { "X-Requested-With": "XMLHttpRequest" },
      success: (response) => {
        if (response.success) {
          this.emailSent = true;
          this.hasUnsavedChanges = false;

          this.showNotification("Email sent successfully!", "success");
          setTimeout(() => {
            this.close();
          }, 2000);
        } else {
          this.showNotification(
            response.message || "Failed to send email",
            "error"
          );
        }
      },
      error: (xhr) => {
        const errorMsg = xhr.responseJSON?.message || "Error sending email";
        this.showNotification(errorMsg, "error");
      },
    });
  }

  showNotification(message, type) {
    $(".email-notification").remove();

    const notification = $(`
      <div class="email-notification ${type}">
        ${message}
      </div>
    `);

    $("#emailComposer").append(notification);

    setTimeout(() => {
      notification.fadeOut(300, function () {
        $(this).remove();
      });
    }, 3000);
  }
}

let emailComposer;
$(document).ready(function () {
  emailComposer = new EmailComposer();
});
