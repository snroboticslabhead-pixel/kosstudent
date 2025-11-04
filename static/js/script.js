// static/script.js
// Initialize CodeMirror editor
let editor = CodeMirror(document.getElementById("editor"), {
  value: `void setup() {
  // put your setup code here
}

void loop() {
  // put your main code here
}`,
  mode: "text/x-c++src",
  lineNumbers: true,
  tabSize: 2,
  indentUnit: 2,
  smartIndent: true,
  matchBrackets: true,
  autoCloseBrackets: true,
  autofocus: true,
  lineWrapping: true,
  theme: "default"
});

editor.scrollTo(0, 0);

const output = document.getElementById("output");
const languageSelect = document.getElementById("language");
const filename = document.getElementById("filename");
const lineCount = document.getElementById("lineCount");
const statusIndicator = document.getElementById("statusIndicator");
const librariesInput = document.getElementById("libraries");
const installBtn = document.getElementById("installBtn");
const compileBtn = document.getElementById("compileBtn");
const submitBtn = document.getElementById("submitBtn");
const clearBtn = document.getElementById("clearBtn");
const librariesControls = document.querySelector(".libraries-controls");

// Update line count
function updateLineCount() {
  lineCount.textContent = editor.lineCount();
}
updateLineCount();
editor.on("change", updateLineCount);

// Switch editor mode based on language
languageSelect.addEventListener("change", () => {
  const lang = languageSelect.value;
  if (lang === "arduino") {
    editor.setOption("mode", "text/x-c++src");
    filename.textContent = "sketch.ino";
    editor.setValue(`void setup() {
  // put your setup code here
}

void loop() {
  // put your main code here
}`);
    librariesInput.placeholder = "Libraries (e.g., Servo, Wire)";
    librariesControls.style.display = "flex";
    editor.scrollTo(0, 0);
  } else if (lang === "python") {
    editor.setOption("mode", "python");
    filename.textContent = "script.py";
    editor.setValue(`print("Hello World")`);
    librariesInput.placeholder = "Packages (e.g., numpy, pandas)";
    librariesControls.style.display = "flex";
    editor.scrollTo(0, 0);
  }
  updateLineCount();
});

// Install Libraries button click
installBtn.addEventListener("click", async () => {
  const libraries = librariesInput.value.split(",").map(lib => lib.trim()).filter(lib => lib);
  const lang = languageSelect.value;

  if (libraries.length === 0) {
    output.textContent = "No libraries specified.";
    output.style.color = "#6c757d";
    return;
  }

  statusIndicator.className = "status-indicator status-running";
  output.textContent = `Installing ${lang === "arduino" ? "Arduino" : "Python"} libraries...`;
  output.style.color = "#495057";

  const endpoint = lang === "arduino" ? "/install_libraries" : "/install_python_libs";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ libraries })
    });

    const data = await response.json();

    if (data.status === "success") {
      statusIndicator.className = "status-indicator status-success";
      output.textContent = `✓ ${lang === "arduino" ? "Arduino" : "Python"} libraries installed successfully\n\n` + data.output;
      output.style.color = "#198754";
    } else {
      statusIndicator.className = "status-indicator status-error";
      output.textContent = `✗ Installation Error\n\n` + data.output;
      output.style.color = "#dc3545";
    }
  } catch (err) {
    statusIndicator.className = "status-indicator status-error";
    output.textContent = "✗ Network Error\n\n" + err.message;
    output.style.color = "#dc3545";
  }
});

// Compile / Run button click
compileBtn.addEventListener("click", async () => {
  const code = editor.getValue();
  const lang = languageSelect.value;

  statusIndicator.className = "status-indicator status-running";
  output.textContent = `Compiling and running ${lang === "arduino" ? "Arduino" : "Python"} code...`;
  output.style.color = "#495057";

  const endpoint = lang === "arduino" ? "/compile/arduino" : "/compile/python";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code })
    });

    const data = await response.json();

    if (data.status === "success") {
      statusIndicator.className = "status-indicator status-success";
      output.textContent = "✓ Success\n\n" + data.output;
      output.style.color = "#198754";
      submitBtn.disabled = false;
    } else {
      statusIndicator.className = "status-indicator status-error";
      output.textContent = "✗ Error\n\n" + data.output;
      output.style.color = "#dc3545";
      submitBtn.disabled = true;
    }
  } catch (err) {
    statusIndicator.className = "status-indicator status-error";
    output.textContent = "✗ Network Error\n\n" + err.message;
    output.style.color = "#dc3545";
    submitBtn.disabled = true;
  }
});

// Clear Output
clearBtn.addEventListener("click", () => {
  output.textContent = "Output will appear here...";
  output.style.color = "#6c757d";
  statusIndicator.className = "";
  submitBtn.disabled = true;
});

// Disable submit initially
submitBtn.disabled = true;