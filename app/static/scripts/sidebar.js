// Load residents for the sidebar
$(document).ready(function() {
    // Only execute if the sidebar exists and doesn't already have residents
    if ($('#residents-list').length && $('#residents-list .sidebar-item').length === 0) {
        $.ajax({
            url: '/api/residents',
            method: 'GET',
            success: function(data) {
                // Clear any existing items
                $('#residents-list').empty();
                
                // Add each resident to the sidebar
                data.residents.forEach(function(resident) {
                    const photoUrl = resident.photo_url || '/static/images/default-profile.png';
                    const residentItem = `
                        <a href="/quick_actions/${resident.id}" class="text-decoration-none">
                            <div class="sidebar-item d-flex align-items-center">
                                <img src="${photoUrl}"
                                     class="rounded-circle me-2" 
                                     style="width: 30px; height: 30px; object-fit: cover;">
                                <span>${resident.name}</span>
                            </div>
                        </a>
                    `;
                    $('#residents-list').append(residentItem);
                });
            },
            error: function(error) {
                console.error('Failed to load residents:', error);
            }
        });
    }
});
