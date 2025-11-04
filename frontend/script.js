const scanBtn = document.getElementById("scanBtn");
const fileInput = document.getElementById("fileInput");
const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");
const logsBody = document.getElementById("logsBody");

const API_BASE = "http://127.0.0.1:5000/api"; // Flask backend

// 🧩 Scan File
scanBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    alert("Please select a file to scan.");
    return;
  }

  loadingDiv.classList.remove("hidden");
  resultDiv.classList.add("hidden");
  resultDiv.innerHTML = "";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/scan_file`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    loadingDiv.classList.add("hidden");

    if (data.error) {
      resultDiv.classList.remove("hidden");
      resultDiv.classList.add("danger");
      resultDiv.innerText = `❌ Error: ${data.error}`;
      return;
    }

    const safe = data.result.includes("Safe");
    resultDiv.className = `result-box ${safe ? "safe" : "danger"}`;
    resultDiv.innerText = `${data.result}`;
    resultDiv.classList.remove("hidden");

    // Refresh logs after scanning
    loadLogs();
  } catch (err) {
    loadingDiv.classList.add("hidden");
    alert("Failed to connect to backend. Please check app.py is running.");
    console.error(err);
  }
});

// 📜 Load Logs
async function loadLogs() {
  try {
    const res = await fetch(`${API_BASE}/logs`);
    const logs = await res.json();

    logsBody.innerHTML = "";
    logs.reverse().forEach((log) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${log.filename}</td>
        <td>${log.result}</td>
        <td>${new Date(log.timestamp).toLocaleString()}</td>
      `;
      logsBody.appendChild(row);
    });
  } catch (err) {
    console.error("Error loading logs:", err);
  }
}

// Load logs initially
loadLogs();
