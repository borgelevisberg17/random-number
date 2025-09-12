document.addEventListener('DOMContentLoaded', () => {
    // Função para exibir mensagens
    function showMessage(elementId, message, type) {
        const messageDiv = document.getElementById(elementId);
        const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info';
        messageDiv.innerHTML += `<div class="alert ${alertClass}">${message}</div>`;
        messageDiv.scrollTop = messageDiv.scrollHeight;
    }

    // Função para exibir pontuações
    function showScores(scores, mode) {
        const scoresDiv = document.getElementById('scores');
        let html = '<h5 class="text-light">Pontuações:</h5><ul class="list-group">';
        if (mode === '2x2' || mode === 'tournament_2x2') {
            const teams = {};
            for (const [player, score] of Object.entries(scores)) {
                if (player.startsWith('team_')) {
                    html += `<li class="list-group-item list-group-item-dark">Equipe ${player.replace('team_', '')}: ${score} pontos</li>`;
                } else {
                    teams[player] = teams[player] || { players: [], score: 0 };
                    teams[player].players.push(`${player}: ${score}`);
                }
            }
            for (const team of Object.values(teams)) {
                team.players.forEach(p => {
                    html += `<li class="list-group-item list-group-item-dark">${p}</li>`;
                });
            }
        } else {
            for (const [player, score] of Object.entries(scores)) {
                html += `<li class="list-group-item list-group-item-dark">${player}: ${score} pontos</li>`;
            }
        }
        html += '</ul>';
        scoresDiv.innerHTML = html;
    }

    // Função para criar gráfico de barras
    let chartInstance = null;
    function createChart(canvasId, data, labels, title) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;
        if (chartInstance) chartInstance.destroy();
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: title,
                    data: data,
                    backgroundColor: '#28a745',
                    borderColor: '#218838',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Pontuação', color: '#ffffff' },
                        ticks: { color: '#ffffff' }
                    },
                    x: {
                        title: { display: true, text: 'Jogador/Equipe', color: '#ffffff' },
                        ticks: { color: '#ffffff' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#ffffff' } },
                    title: { display: true, text: title, color: '#ffffff' }
                }
            }
        });
    }

    // Função para exibir chaves de torneio
    function showTournamentBracket(players, phase) {
        const bracketDiv = document.getElementById('tournament-bracket');
        if (!bracketDiv) return;
        let html = `<h5 class="text-light">${phase === 'semifinals' ? 'Semifinais' : 'Final'}</h5>`;
        if (phase === 'semifinals') {
            html += `
                <div class="bracket-match">
                    <div class="bracket-player">${players[0]} vs ${players[1]}</div>
                </div>
                <div class="bracket-match">
                    <div class="bracket-player">${players[2]} vs ${players[3]}</div>
                </div>`;
        } else {
            html += `<div class="bracket-match"><div class="bracket-player">${players[0]} vs ${players[1]}</div></div>`;
        }
        bracketDiv.innerHTML = html;
        bracketDiv.style.display = 'block';
    }

    // Singleplayer
    const startForm = document.getElementById('start-form');
    const gameControls = document.getElementById('game-controls');
    const submitGuess = document.getElementById('submit-guess');
    let gameState = null;

    if (startForm && !startForm.dataset.multiplayer && !startForm.dataset.tournament && !startForm.dataset.training) {
        startForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const playerName = document.getElementById('player_name')?.value;
            const difficulty = document.getElementById('difficulty').value;
            try {
                const response = await fetch('/singleplayer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_name: playerName, difficulty })
                });
                const data = await response.json();
                showMessage('game-messages', data.message, data.status);
                if (data.status === 'start') {
                    gameState = data.game_state;
                    startForm.style.display = 'none';
                    gameControls.style.display = 'block';
                }
            } catch (error) {
                showMessage('game-messages', 'Erro ao iniciar o jogo!', 'error');
            }
        });

        if (submitGuess) {
            submitGuess.addEventListener('click', async () => {
                const guess = document.getElementById('guess').value;
                try {
                    const response = await fetch('/singleplayer', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: gameState.name, guess, game_state: gameState })
                    });
                    const data = await response.json();
                    showMessage('game-messages', data.message, data.status);
                    if (data.status === 'game_over') {
                        gameControls.style.display = 'none';
                        startForm.style.display = 'block';
                    } else if (data.status !== 'error') {
                        gameState = data.game_state || gameState;
                    }
                } catch (error) {
                    showMessage('game-messages', 'Erro ao enviar palpite!', 'error');
                }
            });
        }
    }

    // Multiplayer, Torneio e Treinamento
    let socket = null;
    if (startForm && (startForm.dataset.multiplayer || startForm.dataset.tournament || startForm.dataset.training)) {
        const mode = startForm.dataset.multiplayer || startForm.dataset.tournament || startForm.dataset.training;
        socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

        socket.on('game_message', (data) => {
            showMessage('game-messages', data.message, data.status);
            if (data.status === 'joined' && data.player === document.getElementById('player_name').value) {
                startForm.style.display = 'none';
                gameControls.style.display = 'block';
            }
        });

        socket.on('game_start', (data) => {
            showMessage('game-messages', data.message, 'info');
            const playerName = document.getElementById('player_name').value;
            submitGuess.disabled = data.current_player !== playerName;
            if (mode === 'tournament_1x1') {
                showTournamentBracket(Object.keys(data.game_state.players), data.phase);
            }
        });

        socket.on('game_update', (data) => {
            showMessage('game-messages', data.message, 'info');
            const playerName = document.getElementById('player_name').value;
            submitGuess.disabled = data.current_player !== playerName;
            if (mode === 'tournament_1x1') {
                showTournamentBracket(Object.keys(data.game_state.players), data.phase);
            }
        });

        socket.on('game_over', (data) => {
            showMessage('game-messages', data.message, 'success');
            showScores(data.scores, mode);
            gameControls.style.display = 'none';
            document.getElementById('rematch').style.display = 'block';
            startForm.style.display = 'block';
            if (startForm.dataset.training) {
                const scores = Object.entries(data.scores).filter(([k]) => !k.startsWith('team_'));
                createChart('training-chart', scores.map(s => s[1]), scores.map(s => s[0]), 'Progresso do Treino');
                document.getElementById('training-chart').style.display = 'block';
            }
        });

        startForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const trainingMode = document.getElementById('mode')?.value || mode;
            const difficulty = document.getElementById('difficulty').value;
            const rounds = document.getElementById('rounds').value;
            const sessionId = document.getElementById('session_id').value || '';
            const playerName = document.getElementById('player_name').value;
            const players = {};
            let team1_name, team2_name;

            if (trainingMode === '1x1') {
                players.player2 = document.getElementById('player2')?.value;
            } else if (trainingMode === '2x2') {
                team1_name = document.getElementById('team1_name')?.value;
                players.team1_p2 = document.getElementById('team1_p2')?.value;
                team2_name = document.getElementById('team2_name')?.value;
                players.team2_p1 = document.getElementById('team2_p1')?.value;
                players.team2_p2 = document.getElementById('team2_p2')?.value;
                players.team1_p1 = playerName;
            } else {
                players.player1 = playerName;
            }

            try {
                const endpoint = startForm.dataset.tournament ? '/tournament' : startForm.dataset.training ? '/training' : '/multiplayer';
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        mode: trainingMode,
                        difficulty,
                        rounds,
                        players,
                        team1_name,
                        team2_name,
                        session_id: sessionId,
                        player_name: playerName
                    })
                });
                const data = await response.json();
                showMessage('game-messages', data.message, data.status);
                if (data.status === 'start') {
                    socket.emit('join_game', { session_id: data.session_id, player: playerName });
                }
            } catch (error) {
                showMessage('game-messages', 'Erro ao iniciar o jogo!', 'error');
            }
        });

        if (document.getElementById('mode')) {
            document.getElementById('mode').addEventListener('change', () => {
                const multiplayerFields = document.getElementById('multiplayer-fields');
                multiplayerFields.style.display = document.getElementById('mode').value !== 'singleplayer' ? 'block' : 'none';
            });
        }

        submitGuess.addEventListener('click', () => {
            const guess = document.getElementById('guess').value;
            const sessionId = document.getElementById('session_id').value;
            const playerName = document.getElementById('player_name').value;
            socket.emit('submit_guess', { session_id: sessionId, player: playerName, guess });
        });

        document.getElementById('rematch').addEventListener('click', () => {
            const sessionId = document.getElementById('session_id').value;
            socket.emit('rematch', { session_id: sessionId });
            document.getElementById('rematch').style.display = 'none';
            showMessage('game-messages', 'Revanche solicitada!', 'info');
        });
    }

    // Online
    if (document.getElementById('online-form')) {
        socket = socket || io.connect(location.protocol + '//' + document.domain + ':' + location.port);
        const onlineForm = document.getElementById('online-form');
        const modeSelect = document.getElementById('mode');
        const teamField = document.getElementById('team-field');

        socket.on('online_status', (data) => {
            const statusDiv = document.getElementById('online-status');
            let html = '<h5 class="text-light">Status Online:</h5><ul class="list-group">';
            data.players.forEach(p => {
                html += `<li class="list-group-item list-group-item-dark">${p.name}${p.team ? ` (Equipe ${p.team})` : ''}: ${p.status}</li>`;
            });
            html += '</ul>';
            statusDiv.innerHTML = html;
        });

        socket.on('game_message', (data) => {
            showMessage('game-messages', data.message, data.status);
            if (data.status === 'joined' && data.player === document.getElementById('player').value) {
                onlineForm.style.display = 'none';
                gameControls.style.display = 'block';
            }
        });

        socket.on('game_start', (data) => {
            showMessage('game-messages', data.message, 'info');
            const playerName = document.getElementById('player').value;
            submitGuess.disabled = data.current_player !== playerName;
            if (data.phase && data.game_state.mode === 'tournament_1x1') {
                showTournamentBracket(Object.keys(data.game_state.players), data.phase);
            }
        });

        socket.on('game_update', (data) => {
            showMessage('game-messages', data.message, 'info');
            const playerName = document.getElementById('player').value;
            submitGuess.disabled = data.current_player !== playerName;
            if (data.phase && data.game_state.mode === 'tournament_1x1') {
                showTournamentBracket(Object.keys(data.game_state.players), data.phase);
            }
        });

        socket.on('game_over', (data) => {
            showMessage('game-messages', data.message, 'success');
            showScores(data.scores, data.game_state.mode);
            gameControls.style.display = 'none';
            document.getElementById('rematch').style.display = 'block';
            onlineForm.style.display = 'block';
        });

        modeSelect.addEventListener('change', () => {
            teamField.style.display = modeSelect.value === '2x2' || modeSelect.value === 'tournament_2x2' ? 'block' : 'none';
        });

        onlineForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const player = document.getElementById('player').value;
            const sessionId = document.getElementById('session_id').value;
            const mode = modeSelect.value;
            const team = document.getElementById('team')?.value;
            const difficulty = document.getElementById('difficulty').value;
            const rounds = document.getElementById('rounds').value;
            try {
                const response = await fetch('/online', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player, session_id: sessionId, mode, team, difficulty, rounds })
                });
                const data = await response.json();
                showMessage('game-messages', data.message, data.status);
                if (data.status === 'start') {
                    socket.emit('join_game', { session_id: data.session_id, player });
                }
            } catch (error) {
                showMessage('game-messages', 'Erro ao conectar à Arena Online!', 'error');
            }
        });

        submitGuess.addEventListener('click', () => {
            const guess = document.getElementById('guess').value;
            const sessionId = document.getElementById('session_id').value;
            const playerName = document.getElementById('player').value;
            socket.emit('submit_guess', { session_id: sessionId, player: playerName, guess });
        });

        document.getElementById('rematch').addEventListener('click', () => {
            const sessionId = document.getElementById('session_id').value;
            socket.emit('rematch', { session_id: sessionId });
            document.getElementById('rematch').style.display = 'none';
            showMessage('game-messages', 'Revanche solicitada!', 'info');
        });
    }

    // Wi-Fi Management
    const wifiForm = document.getElementById('wifi-form');
    if (wifiForm) {
        const actionSelect = document.getElementById('action');
        const nameField = document.getElementById('name-field');
        actionSelect.addEventListener('change', () => {
            nameField.style.display = actionSelect.value === 'list' ? 'none' : 'block';
        });

        wifiForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const action = actionSelect.value;
            const name = document.getElementById('name')?.value;
            try {
                const response = await fetch('/wifi', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action, name })
                });
                const data = await response.json();
                showMessage('wifi-messages', data.message, data.status);
                if (action === 'list') {
                    const playerList = document.getElementById('player-list');
                    playerList.innerHTML = `<h5 class="text-light">Jogadores na Rede:</h5><ul class="list-group">${data.players.map(p => `<li class="list-group-item list-group-item-dark">${p}</li>`).join('')}</ul>`;
                }
            } catch (error) {
                showMessage('wifi-messages', 'Erro ao gerenciar jogadores!', 'error');
            }
        });
    }

    // Ranking
    const rankTypeSelect = document.getElementById('rank-type');
    const playerField = document.getElementById('player-field');
    const showRanking = document.getElementById('show-ranking');
    if (rankTypeSelect) {
        rankTypeSelect.addEventListener('change', () => {
            playerField.style.display = rankTypeSelect.value === 'player' ? 'block' : 'none';
        });

        showRanking.addEventListener('click', async () => {
            const rankType = rankTypeSelect.value;
            const playerName = document.getElementById('player-name')?.value;
            try {
                const response = await fetch('/ranking', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: rankType, player: playerName })
                });
                const data = await response.json();
                const rankingTable = document.getElementById('ranking-table');
                let html = '<table class="table table-dark">';
                let chartData = [];
                let chartLabels = [];
                let chartTitle = '';

                if (rankType === 'history') {
                    html += '<thead><tr><th>Jogador</th><th>Equipe</th><th>Vitórias</th><th>Pontuação</th><th>Data</th><th>Tipo</th></tr></thead><tbody>';
                    data.scores.forEach(row => {
                        const className = row[0] === data.current_player ? 'current-player' : '';
                        html += `<tr class="${className}"><td>${row[0]}</td><td>${row[1] || '-'}</td><td>${row[2]}</td><td>${row[3]}</td><td>${row[4]}</td><td>${row[5]}</td></tr>`;
                    });
                } else if (rankType.includes('multiplayer_2x2') || rankType.includes('tournament_2x2')) {
                    html += '<thead><tr><th>Equipe</th><th>Jogador</th><th>Vitórias</th><th>Pontuação Média</th><th>Última Partida</th><th>Badge</th></tr></thead><tbody>';
                    data.scores.forEach(row => {
                        const className = row[1] === data.current_player ? 'current-player' : '';
                        html += `<tr class="${className}"><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td><td>${row[4]}</td><td>${row[5]}</td></tr>`;
                        chartData.push(parseFloat(row[3]));
                        chartLabels.push(`${row[0]} (${row[1]})`);
                    });
                    chartTitle = rankType.includes('multiplayer_2x2') ? 'Ranking Multiplayer 2x2' : 'Ranking Torneio 2x2';
                } else if (rankType.includes('multiplayer_1x1') || rankType.includes('tournament_1x1')) {
                    html += '<thead><tr><th>Jogador</th><th>Vitórias</th><th>Pontuação Média</th><th>Última Partida</th><th>Badge</th></tr></thead><tbody>';
                    data.scores.forEach(row => {
                        const className = row[0] === data.current_player ? 'current-player' : '';
                        html += `<tr class="${className}"><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td><td>${row[3]}</td><td>${row[4]}</td></tr>`;
                        chartData.push(parseFloat(row[2]));
                        chartLabels.push(row[0]);
                    });
                    chartTitle = rankType.includes('multiplayer_1x1') ? 'Ranking Multiplayer 1x1' : 'Ranking Torneio 1x1';
                } else {
                    html += '<thead><tr><th>Jogador</th><th>Tentativas</th><th>Data</th></tr></thead><tbody>';
                    data.scores.forEach(row => {
                        const className = row[0] === data.current_player ? 'current-player' : '';
                        html += `<tr class="${className}"><td>${row[0]}</td><td>${row[1]}</td><td>${row[2]}</td></tr>`;
                        chartData.push(row[1]);
                        chartLabels.push(row[0]);
                    });
                    chartTitle = rankType === 'global' ? 'Ranking Global' : rankType === 'day' ? 'Ranking do Dia' : rankType === 'week' ? 'Ranking da Semana' : 'Meu Ranking';
                }
                html += '</tbody></table>';
                if (rankType !== 'history') {
                    html += '<canvas id="ranking-chart"></canvas>';
                }
                rankingTable.innerHTML = html;
                if (rankType !== 'history') {
                    document.getElementById('ranking-chart').style.display = 'block';
                    createChart('ranking-chart', chartData, chartLabels, chartTitle);
                } else {
                    document.getElementById('ranking-chart').style.display = 'none';
                }
            } catch (error) {
                showMessage('ranking-table', 'Erro ao carregar ranking!', 'error');
            }
        });
    }
});