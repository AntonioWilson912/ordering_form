class EmailComposer {
  constructor() {
    this.isMinimized = false;
    this.orderData = null;
    this.hasDraft = false;
    this.hasUnsavedChanges = false;
    this.emailSent = false;
    this.init();
  }

  init() {
    // Create composer HTML - Note: No "From" field anymore
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

                        <div class="form-group">
                            <label for="emailTo">To:</label>
                            <input type="email" id="emailTo" name="to" class="form-control" required>
                            <small class="form-text">Recipient email address</small>
                        </div>

                        <div class="form-group sender-info">
                            <label>From:</label>
                            <div class="sender-display">
                                <span id="senderName">Loading...</span>
                                <small class="form-text">Replies will be sent to your email address</small>
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="emailSubject">Subject:</label>
                            <input type="text" id="emailSubject" name="subject" class="form-control"
                                   value="Order Request" required>
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

    // Minimize/Maximize - only on title
    $("#emailHeaderTitle").click(function () {
      self.toggleMinimize();
    });

    // Prevent header click when clicking controls
    $(".email-controls").click(function (e) {
      e.stopPropagation();
    });

    // Close
    $("#closeEmail").click(function () {
      self.close();
    });

    // Minimize button
    $("#minimizeEmail").click(function () {
      self.toggleMinimize();
    });

    // Save Draft
    $("#saveDraft").click(function () {
      self.saveDraft();
    });

    // Send Email
    $("#emailForm").submit(function (e) {
      e.preventDefault();
      self.sendEmail();
    });

    // Track changes for unsaved warning
    $("#emailTo, #emailSubject, #emailContent").on("input change", function () {
      self.hasUnsavedChanges = true;
      // Hide draft indicator when content changes after saving
      if (self.hasDraft) {
        $("#draftIndicator").hide();
        self.hasDraft = false;
      }
    });
  }

  async loadUserInfo() {
    try {
      const response = await $.ajax({
        url: "/api/user/email-info/",
        type: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (response.success) {
        $("#senderName").text(response.sender_name);
        this.userInfo = response;
      }
    } catch (error) {
      console.error("Failed to load user info:", error);
      $("#senderName").text("Order Form");
    }
  }

  async open(orderData, companyEmail) {
    this.orderData = orderData;
    this.hasUnsavedChanges = false;
    this.emailSent = false;

    // Load user info for sender display
    await this.loadUserInfo();

    // Set order ID
    $("#orderId").val(orderData.order_id);

    // Try to load existing draft first
    const hasDraft = await this.loadDraft(orderData.order_id);

    if (!hasDraft) {
      // No draft found, use template
      $("#emailTo").val(companyEmail || "");
      $("#emailSubject").val("Order Request");

      const content = this.generateEmailContent(orderData);
      $("#emailContent").val(content);

      this.hasDraft = false;
      this.hasUnsavedChanges = false;
      $("#draftIndicator").hide();
    }

    // Show composer
    $("#emailComposer").addClass("show").fadeIn(300);
  }

  async loadDraft(orderId) {
    try {
      const response = await $.ajax({
        url: `/api/orders/${orderId}/draft/`,
        type: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (response.success && response.draft) {
        // Load draft data
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
      console.log("No draft found, using template");
      return false;
    }
  }

  generateEmailContent(orderData) {
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
    // Only show warning if:
    // 1. There are unsaved changes
    // 2. Email was NOT sent (sending clears the flag)
    // 3. No draft has been saved
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
    };

    // Add CSRF token
    formData.csrfmiddlewaretoken = $("[name=csrfmiddlewaretoken]").val();

    $.ajax({
      url: "/api/orders/save-draft/",
      type: "POST",
      data: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
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
        console.error("Error saving draft:", xhr);
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
    };

    // Add CSRF token
    formData.csrfmiddlewaretoken = $("[name=csrfmiddlewaretoken]").val();

    $.ajax({
      url: "/api/orders/send-email/",
      type: "POST",
      data: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      success: (response) => {
        if (response.success) {
          // Mark email as sent - this prevents the "unsaved changes" warning
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
        console.error("Error sending email:", xhr);
        const errorMsg = xhr.responseJSON?.message || "Error sending email";
        this.showNotification(errorMsg, "error");
      },
    });
  }

  showNotification(message, type) {
    // Remove existing notifications
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

// Initialize email composer when document is ready
let emailComposer;
$(document).ready(function () {
  emailComposer = new EmailComposer();
});
