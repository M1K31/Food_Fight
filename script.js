document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const preferencesForm = document.getElementById('preferences-form');
    const distanceSlider = document.getElementById('distance');
    const distanceValue = document.getElementById('distance-value');
    const tournamentContainer = document.getElementById('tournament-container');
    const winnerDisplay = document.getElementById('winner-display');
    const winnerSection = document.getElementById('winner-section');
    const tournamentSection = document.getElementById('tournament-section');

    // State
    let currentBracket = [];

    // Event Listeners
    distanceSlider.addEventListener('input', () => {
        distanceValue.textContent = `${distanceSlider.value} miles`;
    });

    preferencesForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const preferences = {
            cuisine: e.target.cuisine.value,
            budget: parseInt(e.target.budget.value, 10),
            distance: parseInt(e.target.distance.value, 10)
        };
        startTournament(preferences);
    });

    // Event Delegation for Vote Buttons
    tournamentContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('vote-button')) {
            handleVote(e.target.closest('.option'));
        }
    });


    // Main Functions
    function filterRestaurants(preferences) {
        let filtered = restaurants.filter(r => {
            const cuisineMatch = preferences.cuisine === 'any' || r.cuisine === preferences.cuisine;
            const budgetMatch = isNaN(preferences.budget) || r.budget <= preferences.budget;
            const distanceMatch = r.distance <= preferences.distance;
            return cuisineMatch && budgetMatch && distanceMatch;
        });
        filtered.sort((a, b) => b.rating - a.rating);
        const bracketSize = Math.pow(2, Math.floor(Math.log2(filtered.length)));
        return filtered.slice(0, Math.max(2, bracketSize));
    }

    function startTournament(preferences) {
        const contenders = filterRestaurants(preferences);

        tournamentContainer.innerHTML = '';
        winnerDisplay.innerHTML = '';
        winnerSection.style.display = 'none';
        tournamentSection.style.display = 'block';

        if (contenders.length < 2) {
            tournamentContainer.innerHTML = '<p>Not enough restaurants match your criteria. Please try again.</p>';
            return;
        }

        buildBracket(contenders);
        activateRound(1);
    }

    function buildBracket(contenders) {
        currentBracket = [];
        let rounds = Math.log2(contenders.length);
        let currentContenders = [...contenders];

        for (let i = 0; i < rounds; i++) {
            const roundIndex = i + 1;
            const round = { round: roundIndex, matchups: [] };
            const roundEl = document.createElement('div');
            roundEl.className = 'round';
            roundEl.dataset.roundId = roundIndex;
            roundEl.innerHTML = `<h3 class="round-title">Round ${roundIndex}</h3>`;

            let nextContenders = [];
            for (let j = 0; j < currentContenders.length; j += 2) {
                const matchup = {
                    pair: [currentContenders[j], currentContenders[j + 1]],
                    winner: null,
                    element: createMatchupElement(roundIndex, j / 2, currentContenders[j], currentContenders[j+1])
                };
                round.matchups.push(matchup);
                roundEl.appendChild(matchup.element);
                nextContenders.push(null);
            }
            currentBracket.push(round);
            tournamentContainer.appendChild(roundEl);
            currentContenders = nextContenders;
        }
    }

    function createMatchupElement(roundId, matchupId, option1, option2) {
        const matchupEl = document.createElement('div');
        matchupEl.className = 'matchup';
        matchupEl.dataset.roundId = roundId;
        matchupEl.dataset.matchupId = matchupId;

        // --- FUTURE VIDEO IMPLEMENTATION ---
        // const videoContainer = document.createElement('div');
        // videoContainer.className = 'matchup-video';
        // const video = document.createElement('video');
        // video.loop = true;
        // video.muted = true;
        // video.playsInline = true;
        // videoContainer.appendChild(video);
        // matchupEl.appendChild(videoContainer);
        // ------------------------------------

        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'matchup-options';

        const option1El = createOptionElement(option1, 1);
        const option2El = createOptionElement(option2, 2);

        optionsContainer.appendChild(option1El);
        optionsContainer.appendChild(option2El);
        matchupEl.appendChild(optionsContainer);

        return matchupEl;
    }

    function createOptionElement(restaurant, optionId) {
        const optionEl = document.createElement('div');
        optionEl.className = 'option';
        optionEl.dataset.optionId = optionId;

        if (restaurant) {
            optionEl.innerHTML = `<span class="option-name">${restaurant.name}</span><button class="vote-button" disabled>Vote</button>`;
        } else {
            optionEl.innerHTML = `<span class="option-name placeholder">TBD</span><button class="vote-button" disabled>Vote</button>`;
            optionEl.classList.add('is-placeholder');
        }
        return optionEl;
    }

    function activateRound(roundId) {
        const round = currentBracket.find(r => r.round === roundId);
        if (!round) return;

        round.matchups.forEach(matchup => {
            // --- FUTURE VIDEO IMPLEMENTATION ---
            // const video = matchup.element.querySelector('video');
            // if(video) {
            //     video.src = matchup.pair[0].videoUrl; // Use first contender's video
            //     video.play().catch(e => console.error("Video play failed:", e));
            // }
            // ------------------------------------

            matchup.element.querySelectorAll('.vote-button').forEach(btn => {
                btn.disabled = false;
            });
        });
    }

    function handleVote(selectedOptionEl) {
        if (!selectedOptionEl) return;
        const matchupEl = selectedOptionEl.closest('.matchup');
        const roundId = parseInt(matchupEl.dataset.roundId, 10);
        const matchupId = parseInt(matchupEl.dataset.matchupId, 10);
        const optionId = parseInt(selectedOptionEl.dataset.optionId, 10);

        const round = currentBracket.find(r => r.round === roundId);
        const matchup = round.matchups[matchupId];

        if (matchup.winner) return;

        matchup.winner = matchup.pair[optionId - 1];

        const options = matchupEl.querySelectorAll('.option');
        options.forEach(opt => {
            if (parseInt(opt.dataset.optionId, 10) === optionId) {
                opt.classList.add('winner');
            } else {
                opt.classList.add('loser');
            }
            opt.querySelector('.vote-button').disabled = true;
        });

        const allVoted = round.matchups.every(m => m.winner !== null);
        if (allVoted) {
            if (roundId === currentBracket.length) {
                displayGrandWinner(matchup.winner);
            } else {
                advanceWinners(roundId);
                activateRound(roundId + 1);
            }
        }
    }

    function advanceWinners(completedRoundId) {
        const completedRound = currentBracket.find(r => r.round === completedRoundId);
        const nextRound = currentBracket.find(r => r.round === completedRoundId + 1);

        completedRound.matchups.forEach((matchup, index) => {
            const nextMatchupIndex = Math.floor(index / 2);
            const nextOptionIndex = index % 2;

            const nextMatchupEl = nextRound.matchups[nextMatchupIndex].element;
            const nextOptionEl = nextMatchupEl.querySelectorAll('.option')[nextOptionIndex];

            nextRound.matchups[nextMatchupIndex].pair[nextOptionIndex] = matchup.winner;

            nextOptionEl.classList.remove('is-placeholder');
            nextOptionEl.querySelector('.option-name').textContent = matchup.winner.name;
        });
    }

    function displayGrandWinner(winner) {
        tournamentSection.style.display = 'none';
        winnerSection.style.display = 'block';
        winnerDisplay.innerHTML = `
            <h3>${winner.name}</h3>
            <p>Cuisine: ${winner.cuisine}</p>
            <p>Budget: ${'$'.repeat(winner.budget)}</p>
            <p>Rating: ${winner.rating} / 5</p>
            <p>A truly worthy champion for your dinner!</p>
        `;
    }
});
