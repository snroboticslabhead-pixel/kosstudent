 $(document).ready(function() {
    // Check if user is logged in
    const token = sessionStorage.getItem('token');
    const role = sessionStorage.getItem('role');
    
    if (!token || role !== 'admin') {
        window.location.href = '/';
    }
    
    // Set user info in header
    $.ajax({
        url: '/admin/profile',
        type: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        dataType: 'json', // Explicitly expect JSON
        success: function(response) {
            $('.user-name').text(response.username);
            $('.user-role').text(role);
            sessionStorage.setItem('user', JSON.stringify(response));
        },
        error: function(xhr) {
            console.error('Profile load error:', xhr);
            if (xhr.responseJSON) {
                alert('Error: ' + xhr.responseJSON.message);
            } else {
                alert('Failed to load profile. Please try again.');
            }
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('role');
            window.location.href = '/';
        }
    });
    
    // Page navigation
    $('.menu-item').click(function() {
        const page = $(this).data('page');
        
        // Update active menu item
        $('.menu-item').removeClass('active');
        $(this).addClass('active');
        
        // Update active page
        $('.page').removeClass('active');
        $(`#${page}-page`).addClass('active');
        
        // Load page data
        loadPageData(page);
    });
    
    // Load initial page data
    loadPageData('dashboard');
    
    // Modal handling
    $('.close-modal').click(function() {
        $(this).closest('.modal').removeClass('active');
    });
    
    // Add Student Modal
    $('#add-student-btn').click(function() {
        $('#add-student-modal').addClass('active');
    });
    
    $('#add-student-form').submit(function(e) {
        e.preventDefault();
        
        // Collect form data
        const studentData = {
            name: $('#student-name').val().trim(),
            campus: $('#student-campus').val().trim(),
            grade: $('#student-grade').val().trim(),
            section: $('#student-section').val().trim(),
            password: $('#student-password').val().trim()
        };
        
        // Validate form data
        if (!studentData.name) {
            alert('Please enter a student name');
            return;
        }
        
        if (!studentData.campus) {
            alert('Please select a campus');
            return;
        }
        
        if (!studentData.grade) {
            alert('Please select a grade');
            return;
        }
        
        console.log('Submitting student data:', studentData);
        
        // Show loading state
        const submitBtn = $('#add-student-form button[type="submit"]');
        const originalText = submitBtn.text();
        submitBtn.prop('disabled', true).text('Adding...');
        
        $.ajax({
            url: '/admin/students',
            type: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            dataType: 'json', // Explicitly expect JSON
            data: JSON.stringify(studentData),
            success: function(response) {
                console.log('Student add response:', response);
                
                if (response.success) {
                    alert('Student added successfully!');
                    $('#add-student-modal').removeClass('active');
                    $('#add-student-form')[0].reset();
                    loadPageData('students');
                } else {
                    alert('Error: ' + (response.message || 'Failed to add student'));
                }
            },
            error: function(xhr) {
                console.error('Student add error:', xhr);
                let errorMessage = 'Failed to add student';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            },
            complete: function() {
                // Restore button state
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });
    
    // Upload Students Modal
    $('#upload-students-btn').click(function() {
        $('#upload-students-modal').addClass('active');
    });
    
    $('#upload-students-form').submit(function(e) {
        e.preventDefault();
        
        const fileInput = $('#students-file')[0];
        if (!fileInput.files.length) {
            alert('Please select a file to upload');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        // Show loading state
        const submitBtn = $('#upload-students-form button[type="submit"]');
        const originalText = submitBtn.text();
        submitBtn.prop('disabled', true).text('Uploading...');
        
        $.ajax({
            url: '/admin/students/upload',
            type: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            data: formData,
            processData: false,
            contentType: false,
            dataType: 'json', // Explicitly expect JSON
            success: function(response) {
                if (response.success) {
                    alert(`${response.students.length} students uploaded successfully!`);
                    $('#upload-students-modal').removeClass('active');
                    $('#upload-students-form')[0].reset();
                    loadPageData('students');
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function(xhr) {
                console.error('Upload error:', xhr);
                let errorMessage = 'Failed to upload students';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            },
            complete: function() {
                // Restore button state
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });
    
    // Export Students
    $('#export-students-btn').click(function() {
        window.location.href = `/admin/export/students?token=${token}`;
    });
    
    // Add Task Modal
    $('#add-task-btn').click(function() {
        $('#add-task-modal').addClass('active');
    });
    
    $('#add-task-form').submit(function(e) {
        e.preventDefault();
        
        const campusTargets = [];
        const gradeTargets = [];
        
        $('input[name="campus-target"]:checked').each(function() {
            campusTargets.push($(this).val());
        });
        
        $('input[name="grade-target"]:checked').each(function() {
            gradeTargets.push($(this).val());
        });
        
        if (campusTargets.length === 0) {
            alert('Please select at least one target campus');
            return;
        }
        
        if (gradeTargets.length === 0) {
            alert('Please select at least one target grade');
            return;
        }
        
        const taskData = {
            title: $('#task-title').val().trim(),
            description: $('#task-description').val().trim(),
            language: $('#task-language').val(),
            campusTarget: campusTargets,
            gradeTarget: gradeTargets
        };
        
        // Show loading state
        const submitBtn = $('#add-task-form button[type="submit"]');
        const originalText = submitBtn.text();
        submitBtn.prop('disabled', true).text('Adding...');
        
        $.ajax({
            url: '/admin/tasks',
            type: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            dataType: 'json', // Explicitly expect JSON
            data: JSON.stringify(taskData),
            success: function(response) {
                if (response.success) {
                    alert('Task added successfully!');
                    $('#add-task-modal').removeClass('active');
                    $('#add-task-form')[0].reset();
                    loadPageData('tasks');
                } else {
                    alert('Error: ' + response.message);
                }
            },
            error: function(xhr) {
                console.error('Task add error:', xhr);
                let errorMessage = 'Failed to add task';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            },
            complete: function() {
                // Restore button state
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });
    
    // Generate Report
    $('#generate-report-btn').click(function() {
        const campus = $('#campus-filter').val();
        const grade = $('#grade-filter').val();
        
        $.ajax({
            url: '/admin/reports',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            data: {
                campus: campus,
                grade: grade
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(response) {
                renderReports(response);
            },
            error: function(xhr) {
                console.error('Report generation error:', xhr);
                let errorMessage = 'Failed to generate report';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
    });
    
    // Export Report
    $('#export-report-btn').click(function() {
        const campus = $('#campus-filter').val();
        const grade = $('#grade-filter').val();
        
        window.location.href = `/admin/export/submissions?campus=${campus}&grade=${grade}&token=${token}`;
    });
    
    // Function to load page data
    function loadPageData(page) {
        console.log('Loading page data for:', page);
        
        switch(page) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'students':
                loadStudentsData();
                break;
            case 'tasks':
                loadTasksData();
                break;
            case 'reports':
                loadReportsData();
                break;
        }
    }
    
    // Function to load dashboard data
    function loadDashboardData() {
        console.log('Loading dashboard data');
        
        $.ajax({
            url: '/admin/students',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(students) {
                console.log('Students loaded:', students.length);
                $('#total-students').text(students.length);
                
                // Group students by campus
                const campusGroups = {};
                students.forEach(student => {
                    if (!campusGroups[student.campus]) {
                        campusGroups[student.campus] = [];
                    }
                    campusGroups[student.campus].push(student);
                });
                
                // Render campus cards
                renderCampusCards(campusGroups);
            },
            error: function(xhr) {
                console.error('Failed to load students data:', xhr);
                let errorMessage = 'Failed to load students data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
        
        $.ajax({
            url: '/admin/tasks',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(tasks) {
                console.log('Tasks loaded:', tasks.length);
                $('#total-tasks').text(tasks.length);
            },
            error: function(xhr) {
                console.error('Failed to load tasks data:', xhr);
                let errorMessage = 'Failed to load tasks data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
        
        // Get submission statistics
        $.ajax({
            url: '/admin/reports',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(reports) {
                console.log('Reports loaded:', reports.length);
                let completed = 0;
                let pending = 0;
                
                reports.forEach(report => {
                    completed += report.completed;
                    pending += report.pending;
                });
                
                $('#completed-tasks').text(completed);
                $('#pending-tasks').text(pending);
            },
            error: function(xhr) {
                console.error('Failed to load reports data:', xhr);
                let errorMessage = 'Failed to load reports data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
    }
    
    // Function to render campus cards
    function renderCampusCards(campusGroups) {
        const campusGrid = $('#campus-grid');
        campusGrid.empty();
        
        for (const campus in campusGroups) {
            const students = campusGroups[campus];
            const card = `
                <div class="campus-card">
                    <h3>${campus}</h3>
                    <div class="campus-stats">
                        <div class="campus-stat">
                            <div class="campus-stat-value">${students.length}</div>
                            <div class="campus-stat-label">Students</div>
                        </div>
                        <div class="campus-stat">
                            <div class="campus-stat-value">0</div>
                            <div class="campus-stat-label">Tasks</div>
                        </div>
                        <div class="campus-stat">
                            <div class="campus-stat-value">0%</div>
                            <div class="campus-stat-label">Completion</div>
                        </div>
                    </div>
                    <div class="campus-progress">
                        <div class="campus-progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            `;
            campusGrid.append(card);
        }
    }
    
    // Function to load students data
    function loadStudentsData() {
        console.log('Loading students data');
        
        $.ajax({
            url: '/admin/students',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(students) {
                console.log('Students loaded:', students.length);
                renderStudentsTable(students);
            },
            error: function(xhr) {
                console.error('Failed to load students data:', xhr);
                let errorMessage = 'Failed to load students data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
    }
    
    // Function to render students table
    function renderStudentsTable(students) {
        const tbody = $('#students-table tbody');
        tbody.empty();
        
        if (students.length === 0) {
            tbody.html('<tr><td colspan="6" class="text-center">No students found</td></tr>');
            return;
        }
        
        students.forEach(student => {
            const row = `
                <tr>
                    <td>${student.studentID}</td>
                    <td>${student.name}</td>
                    <td>${student.campus}</td>
                    <td>${student.grade}</td>
                    <td>${student.section || '-'}</td>
                    <td>
                        <button class="action-btn btn-edit" data-id="${student._id}">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="action-btn btn-delete" data-id="${student._id}">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `;
            tbody.append(row);
        });
        
        // Add event listeners to action buttons
        $('.btn-edit').click(function() {
            const studentId = $(this).data('id');
            // Implement edit functionality
            alert('Edit functionality not implemented yet');
        });
        
        $('.btn-delete').click(function() {
            const studentId = $(this).data('id');
            if (confirm('Are you sure you want to delete this student?')) {
                $.ajax({
                    url: `/admin/students/${studentId}`,
                    type: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    dataType: 'json', // Explicitly expect JSON
                    success: function(response) {
                        if (response.success) {
                            alert('Student deleted successfully');
                            loadStudentsData();
                        } else {
                            alert('Error: ' + response.message);
                        }
                    },
                    error: function(xhr) {
                        console.error('Delete student error:', xhr);
                        let errorMessage = 'Failed to delete student';
                        
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMessage = xhr.responseJSON.message;
                        } else if (xhr.statusText) {
                            errorMessage = xhr.statusText;
                        } else if (xhr.responseText) {
                            try {
                                const errorResponse = JSON.parse(xhr.responseText);
                                errorMessage = errorResponse.message || errorMessage;
                            } catch (e) {
                                // If response is not JSON, use status text
                                errorMessage = xhr.statusText || errorMessage;
                            }
                        }
                        
                        alert('Error: ' + errorMessage);
                    }
                });
            }
        });
    }
    
    // Function to load tasks data
    function loadTasksData() {
        console.log('Loading tasks data');
        
        $.ajax({
            url: '/admin/tasks',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(tasks) {
                console.log('Tasks loaded:', tasks.length);
                renderTasksTable(tasks);
            },
            error: function(xhr) {
                console.error('Failed to load tasks data:', xhr);
                let errorMessage = 'Failed to load tasks data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
    }
    
    // Function to render tasks table
    function renderTasksTable(tasks) {
        const tbody = $('#tasks-table tbody');
        tbody.empty();
        
        if (tasks.length === 0) {
            tbody.html('<tr><td colspan="6" class="text-center">No tasks found</td></tr>');
            return;
        }
        
        tasks.forEach(task => {
            const row = `
                <tr>
                    <td>${task.title}</td>
                    <td>${task.description}</td>
                    <td>${task.language}</td>
                    <td>${task.campusTarget.join(', ')}</td>
                    <td>${task.gradeTarget.join(', ')}</td>
                    <td>
                        <button class="action-btn btn-edit" data-id="${task._id}">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="action-btn btn-delete" data-id="${task._id}">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `;
            tbody.append(row);
        });
        
        // Add event listeners to action buttons
        $('.btn-edit').click(function() {
            const taskId = $(this).data('id');
            // Implement edit functionality
            alert('Edit functionality not implemented yet');
        });
        
        $('.btn-delete').click(function() {
            const taskId = $(this).data('id');
            if (confirm('Are you sure you want to delete this task?')) {
                $.ajax({
                    url: `/admin/tasks/${taskId}`,
                    type: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    dataType: 'json', // Explicitly expect JSON
                    success: function(response) {
                        if (response.success) {
                            alert('Task deleted successfully');
                            loadTasksData();
                        } else {
                            alert('Error: ' + response.message);
                        }
                    },
                    error: function(xhr) {
                        console.error('Delete task error:', xhr);
                        let errorMessage = 'Failed to delete task';
                        
                        if (xhr.responseJSON && xhr.responseJSON.message) {
                            errorMessage = xhr.responseJSON.message;
                        } else if (xhr.statusText) {
                            errorMessage = xhr.statusText;
                        } else if (xhr.responseText) {
                            try {
                                const errorResponse = JSON.parse(xhr.responseText);
                                errorMessage = errorResponse.message || errorMessage;
                            } catch (e) {
                                // If response is not JSON, use status text
                                errorMessage = xhr.statusText || errorMessage;
                            }
                        }
                        
                        alert('Error: ' + errorMessage);
                    }
                });
            }
        });
    }
    
    // Function to load reports data
    function loadReportsData() {
        console.log('Loading reports data');
        
        $.ajax({
            url: '/admin/reports',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(reports) {
                console.log('Reports loaded:', reports.length);
                renderReports(reports);
            },
            error: function(xhr) {
                console.error('Failed to load reports data:', xhr);
                let errorMessage = 'Failed to load reports data';
                
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMessage = xhr.responseJSON.message;
                } else if (xhr.statusText) {
                    errorMessage = xhr.statusText;
                } else if (xhr.responseText) {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        errorMessage = errorResponse.message || errorMessage;
                    } catch (e) {
                        // If response is not JSON, use status text
                        errorMessage = xhr.statusText || errorMessage;
                    }
                }
                
                alert('Error: ' + errorMessage);
            }
        });
    }
    
    // Function to render reports
    function renderReports(reports) {
        const tbody = $('#reports-table tbody');
        tbody.empty();
        
        if (reports.length === 0) {
            tbody.html('<tr><td colspan="7" class="text-center">No reports found</td></tr>');
            return;
        }
        
        reports.forEach(report => {
            const completionRate = report.totalStudents > 0 
                ? Math.round((report.completed / report.totalStudents) * 100) 
                : 0;
            
            const row = `
                <tr>
                    <td>${report.task}</td>
                    <td>${report.campus}</td>
                    <td>${report.grade}</td>
                    <td>${report.totalStudents}</td>
                    <td>${report.completed}</td>
                    <td>${report.pending}</td>
                    <td>${completionRate}%</td>
                </tr>
            `;
            tbody.append(row);
        });
    }
    
    // Logout functionality
    $('.btn-logout').click(function(e) {
        e.preventDefault();
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('role');
        sessionStorage.removeItem('user');
        window.location.href = '/';
    });
});