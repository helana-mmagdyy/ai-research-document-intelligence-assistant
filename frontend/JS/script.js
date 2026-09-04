/*
  AI Research & Document Intelligence Assistant
  Frontend Logic

  Backend endpoints:

    POST /upload
      Upload a PDF document.

    POST /chat
      Ask a question about the uploaded documents.

  Expected /upload response:

    {
      success: true,
      document_id: "...",
      filename: "...",
      message: "Document processed successfully."
    }

  Expected /chat response:

    {
      answer: "...",
      sources: [
        {
          filename: "document.pdf",
          page: 1
        }
      ]
    }
*/


// ============================================================
// Configuration
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";


// ============================================================
// Application State
// ============================================================

const state = {
  documents: [],
  messages: [],
};


// ============================================================
// DOM References
// ============================================================

const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const docList = document.getElementById("doc-list");
const shelfEmpty = document.getElementById("shelf-empty");

const statusPill = document.getElementById("status-pill");

const deskTitle = document.getElementById("desk-title");
const deskSub = document.getElementById("desk-sub");

const messagesEl = document.getElementById("messages");
const emptyDesk = document.getElementById("empty-desk");

const composer = document.getElementById("composer");
const composerInput = document.getElementById("composer-input");
const composerSend = document.getElementById("composer-send");

const clearChatBtn = document.getElementById("clear-chat");


// ============================================================
// Upload Handling
// ============================================================


// User selects files
fileInput.addEventListener("change", (event) => {

  handleFiles(event.target.files);

  // Allow selecting the same file again
  fileInput.value = "";

});


// Drag events
["dragenter", "dragover"].forEach((eventName) => {

  dropzone.addEventListener(eventName, (event) => {

    event.preventDefault();
    event.stopPropagation();

    dropzone.classList.add("drag-over");

  });

});


// Remove drag styling
["dragleave", "drop"].forEach((eventName) => {

  dropzone.addEventListener(eventName, (event) => {

    event.preventDefault();
    event.stopPropagation();

    dropzone.classList.remove("drag-over");

  });

});


// Handle dropped files
dropzone.addEventListener("drop", (event) => {

  const files = event.dataTransfer.files;

  handleFiles(files);

});


// Keyboard accessibility
dropzone.addEventListener("keydown", (event) => {

  if (event.key === "Enter" || event.key === " ") {

    event.preventDefault();

    fileInput.click();

  }

});


// ============================================================
// Handle Files
// ============================================================

function handleFiles(fileList) {

  const files = Array.from(fileList);

  const pdfFiles = files.filter((file) => {

    return (
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf")
    );

  });


  // If no PDF was selected
  if (pdfFiles.length === 0) {

    showTemporaryStatus(
      "Please select a PDF file.",
      true
    );

    return;

  }


  // Upload each PDF
  pdfFiles.forEach((file) => {

    const documentItem = {

      // Frontend ID
      id: crypto.randomUUID(),

      // Backend ID will be added after upload
      backendId: null,

      // Original filename
      name: file.name,

      // Status
      status: "processing",

    };


    state.documents.push(documentItem);

    renderDocs();

    updateComposerAvailability();


    // Upload to FastAPI
    uploadDocument(
      file,
      documentItem.id
    );

  });

}


// ============================================================
// Upload Document
// ============================================================

async function uploadDocument(file, docId) {

  try {

    const formData = new FormData();

    formData.append("file", file);


    const response = await fetch(
      `${API_BASE_URL}/upload`,
      {
        method: "POST",
        body: formData,
      }
    );


    if (!response.ok) {

      let errorMessage = "Upload failed.";

      try {

        const errorData = await response.json();

        errorMessage =
          errorData.detail ||
          errorData.error ||
          errorMessage;

      } catch (error) {

        // Ignore JSON parsing error

      }

      throw new Error(errorMessage);

    }


    const result = await response.json();


    console.log(
      "Upload successful:",
      result
    );


    // Backend may return an error with HTTP 200
    if (result.error) {

      throw new Error(
        result.error
      );

    }


    // Find document
    const documentItem = state.documents.find(
      (document) => document.id === docId
    );


    if (documentItem) {

      documentItem.status = "ready";

      documentItem.backendId =
        result.document_id;

      documentItem.filename =
        result.filename ||
        file.name;

    }


  } catch (error) {

    console.error(
      "Document upload error:",
      error
    );


    const documentItem = state.documents.find(
      (document) => document.id === docId
    );


    if (documentItem) {

      documentItem.status = "error";

      documentItem.error =
        error.message;

    }


    showTemporaryStatus(
      error.message ||
      "Failed to process the document.",
      true
    );


  } finally {

    renderDocs();

    updateComposerAvailability();

  }

}


// ============================================================
// Remove Document
// ============================================================

function removeDocument(docId) {

  const documentItem =
    state.documents.find(
      (document) =>
        document.id === docId
    );


  // Remove from frontend state
  state.documents =
    state.documents.filter(
      (document) =>
        document.id !== docId
    );


  // Try to delete from backend
  if (
    documentItem &&
    documentItem.backendId
  ) {

    deleteDocumentFromBackend(
      documentItem.backendId
    );

  }


  renderDocs();

  updateComposerAvailability();

}


// ============================================================
// Delete Document From Backend
// ============================================================

async function deleteDocumentFromBackend(
  backendId
) {

  try {

    const response = await fetch(
      `${API_BASE_URL}/documents/${backendId}`,
      {
        method: "DELETE",
      }
    );


    if (!response.ok) {

      console.error(
        "Failed to delete document from backend."
      );

      return;

    }


    const result =
      await response.json();


    console.log(
      "Document deleted:",
      result
    );


  } catch (error) {

    console.error(
      "Backend document deletion error:",
      error
    );

  }

}


// ============================================================
// Render Documents
// ============================================================

function renderDocs() {

  docList.innerHTML = "";


  const hasDocuments =
    state.documents.length > 0;


  shelfEmpty.hidden =
    hasDocuments;

  docList.hidden =
    !hasDocuments;


  state.documents.forEach((documentItem) => {

    const li =
      document.createElement("li");


    li.className =
      "doc-item";


    if (documentItem.status === "error") {

      li.classList.add("is-error");

    }


    // Status text
    let statusLabel = "Processing";


    if (
      documentItem.status ===
      "ready"
    ) {

      statusLabel = "Ready";

    }


    if (
      documentItem.status ===
      "error"
    ) {

      statusLabel = "Failed to process";

    }


    // Use backend filename if available
    const displayName =
      documentItem.filename ||
      documentItem.name ||
      "Unnamed document";


    // Document HTML
    li.innerHTML = `

      <svg
        class="doc-icon"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        aria-hidden="true"
      >

        <path
          d="M7 3h7l5 5v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1z"
          stroke-linejoin="round"
        />

        <path
          d="M14 3v5h5"
          stroke-linejoin="round"
        />

      </svg>


      <div class="doc-info">

        <div class="doc-name">
          ${escapeHtml(displayName)}
        </div>


        <div class="doc-meta">

          <span
            class="doc-status-dot ${documentItem.status}"
          ></span>

          <span>
            ${statusLabel}
          </span>

        </div>

      </div>


      <button
        class="doc-remove"
        aria-label="Remove ${escapeHtml(displayName)}"
        title="Remove document"
      >

        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          aria-hidden="true"
        >

          <path
            d="M6 6l12 12M18 6L6 18"
            stroke-linecap="round"
          />

        </svg>

      </button>

    `;


    // Remove button
    const removeButton =
      li.querySelector(
        ".doc-remove"
      );


    removeButton.addEventListener(
      "click",
      () => {

        removeDocument(
          documentItem.id
        );

      }
    );


    docList.appendChild(li);

  });


  // Count documents
  const readyCount =
    state.documents.filter(
      (documentItem) =>
        documentItem.status === "ready"
    ).length;


  const processingCount =
    state.documents.filter(
      (documentItem) =>
        documentItem.status ===
        "processing"
    ).length;


  const errorCount =
    state.documents.filter(
      (documentItem) =>
        documentItem.status ===
        "error"
    ).length;


  // Status pill
  if (processingCount > 0) {

    statusPill.textContent =
      `${processingCount} processing`;

    statusPill.classList.add(
      "attention"
    );

  } else if (errorCount > 0 && readyCount === 0) {

    statusPill.textContent =
      `${errorCount} failed`;

    statusPill.classList.add(
      "attention"
    );

  } else {

    statusPill.textContent =
      `${readyCount} ready`;

    statusPill.classList.remove(
      "attention"
    );

  }

}


// ============================================================
// Composer Availability
// ============================================================

function updateComposerAvailability() {

  const hasReadyDocument =
    state.documents.some(
      (documentItem) =>
        documentItem.status ===
        "ready"
    );


  const processing =
    state.documents.some(
      (documentItem) =>
        documentItem.status ===
        "processing"
    );


  composerInput.disabled =
    !hasReadyDocument;


  composerSend.disabled =
    !hasReadyDocument;


  if (hasReadyDocument) {

    composerInput.placeholder =
      "Ask a question about your documents";


    const readyCount =
      state.documents.filter(
        (documentItem) =>
          documentItem.status ===
          "ready"
      ).length;


    deskTitle.textContent =
      "Ask about your documents";


    deskSub.textContent =
      `${readyCount} document(s) ready to search.`;


  } else {

    deskTitle.textContent =
      "Ask about your documents";


    if (processing) {

      deskSub.textContent =
        "Processing your document...";

    } else {

      deskSub.textContent =
        "Upload a PDF on the left, then ask a question here.";

    }


    composerInput.placeholder =
      "Add a document to start asking questions";

  }

}


// ============================================================
// Chat Submission
// ============================================================

composer.addEventListener(
  "submit",
  async (event) => {

    event.preventDefault();


    const question =
      composerInput.value.trim();


    // Empty question
    if (!question) {

      return;

    }


    // Check if a document is ready
    const hasReadyDocument =
      state.documents.some(
        (documentItem) =>
          documentItem.status ===
          "ready"
      );


    if (!hasReadyDocument) {

      return;

    }


    // Clear input
    composerInput.value = "";


    // Add user message
    addMessage(
      "user",
      question
    );


    // Loading message
    const pendingId =
      addPendingMessage();


    // Disable while waiting
    composerInput.disabled =
      true;

    composerSend.disabled =
      true;


    try {

      const result =
        await askQuestion(
          question
        );


      replacePendingMessage(
        pendingId,
        result.answer,
        result.sources || []
      );


    } catch (error) {

      console.error(
        "Chat error:",
        error
      );


      replacePendingMessage(
        pendingId,

        "That question couldn't be answered right now. Please try again in a moment.",

        []
      );

    } finally {

      updateComposerAvailability();

      composerInput.focus();

    }

  }
);


// ============================================================
// Ask Question
// ============================================================

async function askQuestion(question) {

  const response =
    await fetch(
      `${API_BASE_URL}/chat`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({

          question: question,

          history:
            state.messages,

        }),

      }
    );


  if (!response.ok) {

    let errorMessage =
      "Request failed.";


    try {

      const errorData =
        await response.json();


      errorMessage =
        errorData.detail ||
        errorData.error ||
        errorMessage;

    } catch (error) {

      // Ignore JSON parsing error

    }


    throw new Error(
      errorMessage
    );

  }


  const result =
    await response.json();


  console.log(
    "Chat response:",
    result
  );


  // Backend error returned with HTTP 200
  if (result.error) {

    throw new Error(
      result.error
    );

  }


  return {

    answer:
      result.answer ||
      "I couldn't find an answer.",

    sources:
      normalizeSources(
        result.sources || []
      ),

  };

}


// ============================================================
// Normalize Sources
// ============================================================

function normalizeSources(sources) {

  if (!Array.isArray(sources)) {

    return [];

  }


  return sources
    .map((source) => {

      // New backend format:
      //
      // {
      //   filename: "...",
      //   page: 1
      // }

      if (
        source &&
        source.filename
      ) {

        return {

          filename:
            source.filename,

          page:
            source.page,

        };

      }


      // Old backend format:
      //
      // {
      //   label: "document.pdf, p. 1"
      // }

      if (
        source &&
        source.label
      ) {

        return {

          label:
            source.label,

        };

      }


      // Invalid source
      return null;

    })
    .filter(
      (source) =>
        source !== null
    );

}


// ============================================================
// Add Message
// ============================================================

function addMessage(
  role,
  text,
  sources = []
) {

  // Hide empty state
  emptyDesk.hidden = true;


  const messageElement =
    document.createElement("div");


  messageElement.className =
    `msg ${role}`;


  // Prevent HTML injection
  messageElement.textContent =
    text;


  // ==========================================================
  // Sources
  // ==========================================================

  if (
    sources &&
    sources.length > 0
  ) {

    const sourcesElement =
      document.createElement(
        "div"
      );


    sourcesElement.className =
      "sources";


    // Normalize sources
    const normalizedSources =
      normalizeSources(
        sources
      );


    // Remove duplicate sources
    const uniqueSources = [];


    const seenSources =
      new Set();


    normalizedSources.forEach(
      (source) => {

        let sourceKey;


        if (source.filename) {

          sourceKey =
            `${source.filename}|${source.page}`;

        } else {

          sourceKey =
            source.label;

        }


        if (
          !seenSources.has(
            sourceKey
          )
        ) {

          seenSources.add(
            sourceKey
          );

          uniqueSources.push(
            source
          );

        }

      }
    );


    uniqueSources.forEach(
      (source) => {

        const sourceChip =
          document.createElement(
            "span"
          );


        sourceChip.className =
          "source-chip";


        // ====================================================
        // NEW BACKEND FORMAT
        // ====================================================

        if (source.filename) {

          let sourceText =
            `📄 ${source.filename}`;


          if (
            source.page !== undefined &&
            source.page !== null &&
            source.page !== "unknown"
          ) {

            sourceText +=
              ` · Page ${source.page}`;

          }


          sourceChip.textContent =
            sourceText;

        }


        // ====================================================
        // OLD BACKEND FORMAT
        // ====================================================

        else if (source.label) {

          sourceChip.textContent =
            `📄 ${source.label}`;

        }


        // ====================================================
        // FALLBACK
        // ====================================================

        else {

          sourceChip.textContent =
            "📄 Document";

        }


        sourcesElement.appendChild(
          sourceChip
        );

      }
    );


    // Add Sources section only if
    // there are actual source chips
    if (
      uniqueSources.length > 0
    ) {

      messageElement.appendChild(
        sourcesElement
      );

    }

  }


  // Add to chat
  messagesEl.appendChild(
    messageElement
  );


  // Scroll down
  messagesEl.scrollTop =
    messagesEl.scrollHeight;


  // Store message
  state.messages.push({

    role: role,

    content: text,

    text: text,

    sources: sources,

  });


  return messageElement;

}


// ============================================================
// Pending / Loading Message
// ============================================================

function addPendingMessage() {

  emptyDesk.hidden = true;


  const pendingId =
    crypto.randomUUID();


  const messageElement =
    document.createElement(
      "div"
    );


  messageElement.className =
    "msg assistant pending";


  messageElement.dataset.pendingId =
    pendingId;


  messageElement.innerHTML = `

    <span class="dot-flicker">

      <span></span>
      <span></span>
      <span></span>

    </span>

    Searching your documents

  `;


  messagesEl.appendChild(
    messageElement
  );


  messagesEl.scrollTop =
    messagesEl.scrollHeight;


  return pendingId;

}


// ============================================================
// Replace Pending Message
// ============================================================

function replacePendingMessage(
  id,
  answer,
  sources = []
) {

  const pendingElement =
    messagesEl.querySelector(
      `[data-pending-id="${id}"]`
    );


  if (pendingElement) {

    pendingElement.remove();

  }


  addMessage(
    "assistant",
    answer,
    sources
  );

}


// ============================================================
// Clear Conversation
// ============================================================

clearChatBtn.addEventListener(
  "click",
  () => {

    state.messages = [];


    messagesEl.innerHTML = "";


    messagesEl.appendChild(
      emptyDesk
    );


    emptyDesk.hidden = false;

  }
);


// ============================================================
// Temporary Status Message
// ============================================================

function showTemporaryStatus(
  message,
  isError = false
) {

  const originalText =
    statusPill.textContent;


  const originalAttention =
    statusPill.classList.contains(
      "attention"
    );


  statusPill.textContent =
    message;


  statusPill.classList.toggle(
    "attention",
    isError
  );


  setTimeout(
    () => {

      statusPill.textContent =
        originalText;


      statusPill.classList.toggle(
        "attention",
        originalAttention
      );

    },
    3000
  );

}


// ============================================================
// Utilities
// ============================================================

function escapeHtml(str) {

  const div =
    document.createElement(
      "div"
    );


  div.textContent =
    String(str);


  return div.innerHTML;

}


// ============================================================
// Error Handling
// ============================================================

window.addEventListener(
  "error",
  (event) => {

    console.error(
      "Frontend error:",
      event.error
    );

  }
);


// Handle failed API requests
window.addEventListener(
  "unhandledrejection",
  (event) => {

    console.error(
      "Unhandled promise rejection:",
      event.reason
    );

  }
);


// ============================================================
// Initialization
// ============================================================

function initializeApp() {

  renderDocs();

  updateComposerAvailability();

  console.log(
    "AI Research & Document Intelligence Assistant initialized."
  );

  console.log(
    `Backend API: ${API_BASE_URL}`
  );

}


initializeApp();