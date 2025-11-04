 $(document).ready(function() {
    // Check if user is logged in
    const token = sessionStorage.getItem('token');
    const role = sessionStorage.getItem('role');
    
    if (!token || role !== 'student') {
        window.location.href = '/';
    }
    
    // Get task ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('task');
    
    if (!taskId) {
        window.location.href = '/student/dashboard';
    }
    
    // Load task details
    $.ajax({
        url: '/student/tasks',
        type: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        success: function(tasks) {
            const task = tasks.find(t => t._id === taskId);
            if (task) {
                // Update task info
                $('#editor-task-title').text(task.title);
                $('#editor-task-language').text(task.language);
                $('#editor-task-status').text(task.status);
                
                // Set language in editor
                $('#language').val(task.language);
                
                // Load previous submission if exists
                if (task.status === 'completed') {
                    loadPreviousSubmission(taskId);
                } else {
                    // Set default code based on language
                    setDefaultCode(task.language);
                }
            } else {
                alert('Task not found');
                window.location.href = '/student/dashboard';
            }
        },
        error: function() {
            alert('Failed to load task details');
            window.location.href = '/student/dashboard';
        }
    });
    
    // Initialize CodeMirror editor
    let editor = CodeMirror(document.getElementById("editor"), {
        value: "// Loading...",
        mode: "text/x-c++src",
        lineNumbers: true,
        tabSize: 2,
        indentUnit: 2,
        smartIndent: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        autofocus: true,
        lineWrapping: true,
        theme: "monokai"
    });
    
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
            librariesInput.placeholder = "Libraries (e.g., Servo, Wire)";
        } else if (lang === "python") {
            editor.setOption("mode", "python");
            filename.textContent = "script.py";
            librariesInput.placeholder = "Packages (e.g., numpy, pandas)";
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
        
        // Set installing status
        statusIndicator.className = "status-indicator status-running";
        output.textContent = `Installing ${lang === "arduino" ? "Arduino" : "Python"} libraries...`;
        output.style.color = "#495057";
        
        const endpoint = lang === "arduino" ? "/editor/install_libraries" : "/editor/install_python_libs";
        
        try {
            const response = await fetch(endpoint, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
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
        
        // Set running status
        statusIndicator.className = "status-indicator status-running";
        output.textContent = `Compiling and running ${lang === "arduino" ? "Arduino" : "Python"} code...`;
        output.style.color = "#495057";
        
        const endpoint = lang === "arduino" ? "/editor/compile/arduino" : "/editor/compile/python";
        
        try {
            const response = await fetch(endpoint, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ code })
            });
            
            const data = await response.json();
            
            if (data.status === "success") {
                statusIndicator.className = "status-indicator status-success";
                output.textContent = "✓ Success\n\n" + data.output;
                output.style.color = "#198754";
                
                // Enable submit button
                submitBtn.disabled = false;
            } else {
                statusIndicator.className = "status-indicator status-error";
                output.textContent = "✗ Error\n\n" + data.output;
                output.style.color = "#dc3545";
                
                // Disable submit button
                submitBtn.disabled = true;
            }
        } catch (err) {
            statusIndicator.className = "status-indicator status-error";
            output.textContent = "✗ Network Error\n\n" + err.message;
            output.style.color = "#dc3545";
            
            // Disable submit button
            submitBtn.disabled = true;
        }
    });
    
    // Submit button click
    submitBtn.addEventListener("click", async () => {
        const code = editor.getValue();
        const outputText = output.textContent;
        
        if (submitBtn.disabled) {
            return;
        }
        
        try {
            const response = await fetch('/student/submit', {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    taskId: taskId,
                    code: code,
                    output: outputText
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Task submitted successfully!');
                window.location.href = '/student/dashboard';
            } else {
                alert('Error: ' + data.message);
            }
        } catch (err) {
            alert('Network Error: ' + err.message);
        }
    });
    
    // Clear Output
    clearBtn.addEventListener("click", () => {
        output.textContent = "Output will appear here...";
        output.style.color = "#6c757d";
        statusIndicator.className = "";
    });
    
    // Back to tasks button
    $('#back-to-tasks-btn').click(function() {
        window.location.href = '/student/dashboard';
    });
    
    // Function to set default code based on language
    function setDefaultCode(language) {
        if (language === "arduino") {
            editor.setValue(`void setup() {
  // put your setup code here, to run once:
  
}

void loop() {
  // put your main code here, to run repeatedly:
  
}`);
        } else if (language === "python") {
            editor.setValue(`# Write your Python code here
print("Hello, World!")`);
        }
        editor.scrollTo(0, 0);
        updateLineCount();
    }
    
    // Function to load previous submission
    async function loadPreviousSubmission(taskId) {
        try {
            const response = await fetch('/student/tasks', {
                method: "GET",
                headers: { 
                    "Authorization": `Bearer ${token}`
                }
            });
            
            const tasks = await response.json();
            const task = tasks.find(t => t._id === taskId);
            
            if (task && task.status === 'completed') {
                // Load submission details
                const submissionResponse = await fetch(`/student/submission/${taskId}`, {
                    method: "GET",
                    headers: { 
                        "Authorization": `Bearer ${token}`
                    }
                });
                
                const submission = await submissionResponse.json();
                
                if (submission.success) {
                    editor.setValue(submission.code);
                    output.textContent = submission.output;
                    output.style.color = "#198754";
                    statusIndicator.className = "status-indicator status-success";
                    
                    // Enable submit button to allow resubmission
                    submitBtn.disabled = false;
                }
            }
        } catch (err) {
            console.error('Failed to load previous submission:', err);
        }
    }
});