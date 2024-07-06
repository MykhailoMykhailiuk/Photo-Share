document.addEventListener('DOMContentLoaded', () => {
    const loginButton = document.getElementById('login');
    const logoutButton = document.getElementById('logout');

    loginButton.addEventListener('click', () => {
        // Handle login
        alert('Login functionality to be implemented');
    });

    logoutButton.addEventListener('click', () => {
        // Handle logout
        alert('Logout functionality to be implemented');
    });

    // Function to load photos
    function loadPhotos() {
        const photosContainer = document.getElementById('photos');
        const userPhotosContainer = document.getElementById('user-photos');
        
        const photos = [
            { id: 1, url: 'https://via.placeholder.com/150', description: 'Photo 1' },
            { id: 2, url: 'https://via.placeholder.com/150', description: 'Photo 2' },
            { id: 3, url: 'https://via.placeholder.com/150', description: 'Photo 3' }
        ];
        
        photos.forEach(photo => {
            const photoDiv = document.createElement('div');
            const img = document.createElement('img');
            img.src = photo.url;
            img.alt = photo.description;
            const desc = document.createElement('p');
            desc.textContent = photo.description;
            photoDiv.appendChild(img);
            photoDiv.appendChild(desc);

            if (photosContainer) {
                photosContainer.appendChild(photoDiv);
            }

            if (userPhotosContainer) {
                userPhotosContainer.appendChild(photoDiv.cloneNode(true));
            }
        });
    }

    // Call loadPhotos on page load
    loadPhotos();

    // Handle edit profile form submission
    const editProfileForm = document.getElementById('edit-profile-form');
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            alert(`Profile updated: ${username}, ${email}`);
        });
    }
});
