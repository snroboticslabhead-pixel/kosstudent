 $(document).ready(function() {
    // Check if user is logged in
    const token = sessionStorage.getItem('token');
    const role = sessionStorage.getItem('role');
    
    if (!token || role !== 'student') {
        window.location.href = '/';
    }
    
    // Set user info in header
    $.ajax({
        url: '/student/profile',
        type: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        dataType: 'json', // Explicitly expect JSON
        success: function(response) {
            $('.user-name').text(response.name);
            $('.user-role').text(role);
            sessionStorage.setItem('user', JSON.stringify(response));
            
            // Update profile info
            $('#student-name').text(response.name);
            $('#student-id').text(response.studentID);
            $('#student-campus').text(response.campus);
            $('#student-grade').text(response.grade);
            $('#student-section').text(response.section || '-');
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
    
    // View all tasks button
    $('.view-all-btn').click(function(e) {
        e.preventDefault();
        const page = $(this).data('page');
        
        // Update active menu item
        $('.menu-item').removeClass('active');
        $(`.menu-item[data-page="${page}"]`).addClass('active');
        
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
    
    // Task filter
    $('#task-filter').change(function() {
        const filter = $(this).val();
        filterTasks(filter);
    });
    
    // Start task button
    $(document).on('click', '#start-task-btn', function() {
        const taskId = $(this).data('task-id');
        window.location.href = `/editor?task=${taskId}`;
    });
    
    // Function to load page data
    function loadPageData(page) {
        console.log('Loading page data for:', page);
        
        switch(page) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'tasks':
                loadTasksData();
                break;
        }
    }
    
    // Function to load dashboard data
    function loadDashboardData() {
        console.log('Loading dashboard data');
        
        $.ajax({
            url: '/student/tasks',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(tasks) {
                console.log('Tasks loaded:', tasks.length);
                
                // Update stats
                const totalTasks = tasks.length;
                const completedTasks = tasks.filter(task => task.status === 'completed').length;
                const pendingTasks = totalTasks - completedTasks;
                
                $('#total-tasks-count').text(totalTasks);
                $('#completed-tasks-count').text(completedTasks);
                $('#pending-tasks-count').text(pendingTasks);
                
                // Render recent tasks (limit to 4)
                const recentTasks = tasks.slice(0, 4);
                renderRecentTasks(recentTasks);
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
    
    // Function to render recent tasks
    function renderRecentTasks(tasks) {
        const grid = $('#recent-tasks-grid');
        grid.empty();
        
        if (tasks.length === 0) {
            grid.html('<p>No tasks assigned yet.</p>');
            return;
        }
        
        tasks.forEach(task => {
            const card = `
                <div class="task-card">
                    <h3>${task.title}</h3>
                    <p class="task-description">${task.description}</p>
                    <div class="task-meta">
                        <span class="task-language ${task.language}">${task.language}</span>
                        <span class="task-status ${task.status}">${task.status}</span>
                    </div>
                    <div class="task-actions">
                        <button class="btn-view" data-task-id="${task._id}">
                            ${task.status === 'completed' ? 'View' : 'Start'}
                        </button>
                    </div>
                </div>
            `;
            grid.append(card);
        });
        
        // Add event listeners to view buttons
        $('.btn-view').click(function() {
            const taskId = $(this).data('task-id');
            showTaskDetail(taskId);
        });
    }
    
    // Function to load tasks data
    function loadTasksData() {
        console.log('Loading tasks data');
        
        $.ajax({
            url: '/student/tasks',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(tasks) {
                console.log('Tasks loaded:', tasks.length);
                renderTasksList(tasks);
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
    
    // Function to render tasks list
    function renderTasksList(tasks) {
        const list = $('#tasks-list');
        list.empty();
        
        if (tasks.length === 0) {
            list.html('<p>No tasks assigned yet.</p>');
            return;
        }
        
        tasks.forEach(task => {
            const card = `
                <div class="task-card" data-status="${task.status}">
                    <h3>${task.title}</h3>
                    <p class="task-description">${task.description}</p>
                    <div class="task-meta">
                        <span class="task-language ${task.language}">${task.language}</span>
                        <span class="task-status ${task.status}">${task.status}</span>
                    </div>
                    <div class="task-actions">
                        <button class="btn-view" data-task-id="${task._id}">
                            ${task.status === 'completed' ? 'View' : 'Start'}
                        </button>
                    </div>
                </div>
            `;
            list.append(card);
        });
        
        // Add event listeners to view buttons
        $('.btn-view').click(function() {
            const taskId = $(this).data('task-id');
            showTaskDetail(taskId);
        });
    }
    
    // Function to filter tasks
    function filterTasks(filter) {
        if (filter === 'all') {
            $('.task-card').show();
        } else {
            $('.task-card').hide();
            $(`.task-card[data-status="${filter}"]`).show();
        }
    }
    
    // Function to show task detail
    function showTaskDetail(taskId) {
        $.ajax({
            url: '/student/tasks',
            type: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            dataType: 'json', // Explicitly expect JSON
            success: function(tasks) {
                const task = tasks.find(t => t._id === taskId);
                if (task) {
                    $('#modal-task-title').text(task.title);
                    $('#modal-task-language').text(task.language);
                    $('#modal-task-status').text(task.status);
                    $('#modal-task-description').text(task.description);
                    
                    $('#start-task-btn').data('task-id', taskId);
                    $('#task-detail-modal').addClass('active');
                }
            },
            error: function(xhr) {
                console.error('Failed to load task details:', xhr);
                let errorMessage = 'Failed to load task details';
                
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
    
    // Logout functionality
    $('.btn-logout').click(function(e) {
        e.preventDefault();
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('role');
        sessionStorage.removeItem('user');
        window.location.href = '/';
    });
});