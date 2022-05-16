// ==UserScript==
// @name         CSPuz Client
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Connect Penpa+ to a CSPuz backend
// @author       Sam Cappleman-Lynes
// @match        https://swaroopg92.github.io/penpa-edit/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=github.io
// @grant        none
// @require      http://code.jquery.com/jquery-3.6.0.min.js
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    let connectButton = null;
    let dropdown = null;
    let solveButton = null;
    let solverSocket = null;

    const puzzleOptions = [
        {name: 'Kurotto', val: 'kurotto'}
    ];

    const showSolveButton = function() {
        dropdown.attr('style', 'visibility: visible; margin-left: 4px;');
        solveButton.attr('style', 'visibility: visible');
    };

    const hideSolveButton = function() {
        dropdown.attr('style', 'visibility: hidden; margin-left: 4px;');
        solveButton.attr('style', 'visibility: hidden').text('Solve');
    };

    const getSelectedPuzzleType = function() {
        return dropdown.find(':selected').attr('value');
    };

    const clearSolution = function() {
        const oldMode = pu.mode.qa;
        pu.mode.qa = 'pu_a';
        pu.reset_board();
        pu.mode.qa = oldMode;
        pu.redraw();
    };

    const extractKurotto = function() {
        const height = pu.ny - pu.space[0] - pu.space[1];
        const width = pu.nx - pu.space[2] - pu.space[3];
        const numbers = {}
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < height; x++) {
                const index = pu.centerlist[width * y + x];
                if (pu.pu_q.number[index] !== undefined) {
                    numbers[`(${y}, ${x})`] = pu.pu_q.number[index][0];
                }
            }
        }
        return {height, width, numbers};
    };

    const displayKurottoSolution = function(response) {
        const height = response.height;
        const width = response.width;
        for (const [cell, value] of Object.entries(response.shading)) {
            const [y, x] = JSON.parse(cell.replace(/\(/g, "[").replace(/\)/g, "]"));
            const index = pu.centerlist[width * y + x];
            if (value !== null) {
                pu.pu_a.surface[index] = value ? 1 : 2
            }
        }
        pu.redraw();
    };

    const createSocket = function() {
        const socket = new WebSocket('ws://localhost:8765');

        socket.onopen = function() {
            connectButton.text('Disconnect');
            showSolveButton();
        };

        socket.onmessage = function(message) {
            const response = JSON.parse(message.data);
            switch (response.type) {
                case 'kurotto':
                    displayKurottoSolution(response);
                    break;
            }
            solveButton.text('Solve');
        };

        socket.onclose = function() {
            connectButton.text('Connect');
            hideSolveButton();
            solverSocket = null;
        };

        return socket;
    };

    const connect = function() {
        if (!solverSocket) {
            connectButton.text('Connecting...');
            solverSocket = createSocket();
        } else {
            solverSocket.close();
            solverSocket = null;
        };
    };

    const solve = function() {
        if (!!solverSocket) {
            solveButton.text('Solving...');
            clearSolution();
            const type = getSelectedPuzzleType();
            switch (type) {
                case 'kurotto':
                    solverSocket.send(JSON.stringify({...extractKurotto(), type}));
                    break;
                default:
                    solveButton.text('Solve');
            }
        };
    };

    const addSolverMenuAndButtons = function() {

        $('#buttons').append($('<hr size="1" style="margin-top:8px;margin-bottom:8px" noshade>'));
        $('#buttons').append($('<div>').attr('id', 'solver_buttons'));
        $('#solver_buttons').append($('<span><label class="label_mode tooltip" style="font-size: 12px">Solve:</label></span>'));

        connectButton = $('<button>').attr('id', 'connect_button').attr('class', 'label').text('Connect').click(connect);
        $('#solver_buttons').append(connectButton);

        dropdown = $('<select>');
        puzzleOptions.forEach((puzzle) => {
            dropdown.append($('<option>').attr('value', puzzle.val).text(puzzle.name));
        });
        $('#solver_buttons').append(dropdown);

        solveButton = $('<button>').attr('class', 'label').text('Solve').click(solve);
        $('#solver_buttons').append(solveButton);

        hideSolveButton();
    };

    let intervalId = setInterval(() => {
        if (typeof pu === 'undefined') return;
        clearInterval(intervalId);
        addSolverMenuAndButtons();
    }, 20);
})();