document.addEventListener('DOMContentLoaded', () => {
    const preferencesForm = document.getElementById('preferences-form');
    const zipCodeBtn = document.getElementById('zip-code-btn');
    const useLocationBtn = document.getElementById('use-location-btn');

    const battleContainer = document.getElementById('battle-container');
    const winnerDisplay = document.getElementById('winner-display');
    const locationStatus = document.getElementById('location-status');

    // Handle form submission for Zip Code
    preferencesForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const zipCode = document.getElementById('zip-code').value;
        const cuisine = document.getElementById('cuisine').value;
        if (zipCode) {
            startBattle({ zip_code: zipCode, cuisine: cuisine });
        } else {
            locationStatus.textContent = 'Please enter a zip code.';
        }
    });

    // Handle button click for Geolocation
    useLocationBtn.addEventListener('click', () => {
        locationStatus.textContent = 'Getting your location...';
        if (!navigator.geolocation) {
            locationStatus.textContent = 'Geolocation is not supported by your browser.';
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const cuisine = document.getElementById('cuisine').value;
                startBattle({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    cuisine: cuisine
                });
            },
            (error) => {
                locationStatus.textContent = `Error getting location: ${error.message}`;
            }
        );
    });

    async function startBattle(params) {
        // Disable buttons to prevent multiple clicks
        zipCodeBtn.disabled = true;
        useLocationBtn.disabled = true;

        battleContainer.innerHTML = '<p>Loading battle...</p>';
        winnerDisplay.innerHTML = '';
        locationStatus.textContent = 'Finding restaurants...';

        try {
            const response = await fetch('http://localhost:5001/api/battle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Battle could not be started.');
            }

            const data = await response.json();
            displayBattle(data);

        } catch (error) {
            battleContainer.innerHTML = `<p>Error: ${error.message}</p>`;
        } finally {
            // Re-enable buttons
            zipCodeBtn.disabled = false;
            useLocationBtn.disabled = false;
            locationStatus.textContent = '';
        }
    }

    function displayBattle(data) {
        battleContainer.innerHTML = ''; // Clear loading state
        const { winner, images } = data;

        const imageContainer = document.createElement('div');
        imageContainer.className = 'battle-images';
        images.forEach(src => {
            const img = document.createElement('img');
            img.src = src;
            img.alt = 'AI-generated battle scene';
            imageContainer.appendChild(img);
        });
        battleContainer.appendChild(imageContainer);

        winnerDisplay.innerHTML = `
            <h3>'${winner.name}' is the champion!</h3>
            <p><strong>Cuisine:</strong> ${winner.cuisine || 'N/A'}</p>
            <p><strong>Rating:</strong> ${winner.rating ? `${winner.rating.toFixed(1)} / 5.0` : 'N/A'}</p>
            <p><strong>Distance:</strong> ${Math.round(winner.distance)}m away</p>
        `;
    }
});
