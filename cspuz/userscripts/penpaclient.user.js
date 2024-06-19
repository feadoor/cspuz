// ==UserScript==
// @name         CSPuz Client
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Connect Penpa+ to a CSPuz backend
// @author       Sam Cappleman-Lynes
// @match        https://swaroopg92.github.io/penpa-edit/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=github.io
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function() {
    'use strict';

    let connectButton = null;
    let dropdown = null;
    let solveButton = null;
    let solverSocket = null;

    const puzzleOptions = [
        {name: 'Canal View', val: 'canal'},
        {name: 'Guide Arrow', val: 'guidearrow'},
        {name: 'Japanese Sums', val: 'japanesesums'},
        {name: 'Kurotto', val: 'kurotto'},
        {name: 'Kuromasu', val: 'kuromasu'},
        {name: 'Look-Air', val: 'lookair'},
        {name: 'Shakashaka', val: 'shakashaka'},
        {name: 'Yajisan-Kazusan', val: 'yajikazu'},
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

    const getWidth = function() {
        return pu.nx - pu.space[2] - pu.space[3];
    };

    const getHeight = function() {
        return pu.ny - pu.space[0] - pu.space[1];
    };

    const xy_to_index = function(y, x) {
        return pu.nx0 * (y + pu.space[0] + 2) + x + pu.space[2] + 2;
    };

    const index_to_xy = function(index) {
        const x = (index % pu.nx0) - pu.space[2] - 2;
        const y = Math.floor(index / pu.nx0) - pu.space[0] - 2;
        return [x, y];
    };

    const extractNumbers = function() {
        const [width, height, numbers] = [getWidth(), getHeight(), {}];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.number[index] !== undefined) {
                    numbers[`(${y}, ${x})`] = pu.pu_q.number[index][0];
                }
            }
        }
        return numbers;
    };

    const extractShading = function() {
        const [width, height, shading] = [getWidth(), getHeight(), {}];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.surface[index] !== undefined) {
                    shading[`(${y}, ${x})`] = (pu.pu_q.surface[index] !== 2);
                }
            }
        }
        return shading;
    };

    const extractArrowNumbers = function() {
        const [width, height, arrowNumbers] = [getWidth(), getHeight(), {}];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.number[index] !== undefined && pu.pu_q.number[index][0].includes('_') && !pu.pu_q.number[index][0].startsWith('_')) {
                    const [number, dirVal] = pu.pu_q.number[index][0].split('_');
                    const dir = ['U', 'L', 'R', 'D'][parseInt(dirVal, 10)];
                    arrowNumbers[`(${y}, ${x})`] = `(${number}, '${dir}')`;
                }
            }
        }
        return arrowNumbers;
    };

    const extractOutsideTopNumbers = function() {
        const [width, height, outsideNumbers] = [getWidth(), getHeight(), []];
        for (let x = 0; x < width; x++) {
            const numbers = [];
            for (let y = -1; y >= -pu.space[0]; y--) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.number[index] !== undefined) {
                    numbers.push(pu.pu_q.number[index][0]);
                }
            }
            outsideNumbers.push(numbers.reverse());
        }
        return outsideNumbers;
    };

    const extractOutsideLeftNumbers = function() {
        const [width, height, outsideNumbers] = [getWidth(), getHeight(), []];
        for (let y = 0; y < height; y++) {
            const numbers = [];
            for (let x = -1; x >= -pu.space[2]; x--) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.number[index] !== undefined) {
                    numbers.push(pu.pu_q.number[index][0]);
                }
            }
            outsideNumbers.push(numbers.reverse());
        }
        return outsideNumbers;
    };

    const extractJapaneseSumsN = function() {
        const [width, height] = [getWidth(), getHeight()];
        const index = xy_to_index(height, width - 1);
        if (pu.pu_q.number[index] !== undefined) {
            return parseInt(pu.pu_q.number[index], 10);
        } else {
            return 9;
        }
    };

    const extractArrowShapes = function() {
        const [width, height, arrows] = [getWidth(), getHeight(), {}];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.symbol[index] !== undefined && pu.pu_q.symbol[index][1] === 'arrow_B_W') {
                    const dir = ['.', 'L', '.', 'U', '.', 'R', '.', 'D'][pu.pu_q.symbol[index][0]];
                    arrows[`(${y}, ${x})`] = dir;
                }
            }
        }
        return arrows;
    };

    const extractStarLocation = function() {
        const [width, height] = [getWidth(), getHeight()];
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const index = xy_to_index(y, x);
                if (pu.pu_q.symbol[index] !== undefined && pu.pu_q.symbol[index][1] == 'star') {
                    return `(${y}, ${x})`;
                }
            }
        }
        return undefined;
    }

    const displayShading = function(shading) {
        for (const [cell, value] of Object.entries(shading)) {
            const [y, x] = JSON.parse(cell.replace(/\(/g, "[").replace(/\)/g, "]"));
            const index = xy_to_index(y, x);
            if (value !== null) {
                pu.pu_a.surface[index] = value ? 1 : 2
            }
        }
        pu.redraw();
    };

    const displayNumbers = function(numbers) {
        for (const [cell, value] of Object.entries(numbers)) {
            const [y, x] = JSON.parse(cell.replace(/\(/g, "[").replace(/\)/g, "]"));
            const index = xy_to_index(y, x);
            if (value !== null) {
                pu.pu_a.number[index] = [value, 9, '1'];
            }
        }
        pu.redraw();
    };

    const displayTriangles = function(triangles) {
        for (const [cell, value] of Object.entries(triangles)) {
            const [y, x] = JSON.parse(cell.replace(/\(/g, "[").replace(/\)/g, "]"));
            const index = xy_to_index(y, x)
            if (value !== null) {
                if (value === 0) {
                    pu.pu_a.symbol[index] = [8, 'ox_B', 2];
                } else {
                    pu.pu_a.symbol[index] = [value, 'tri', 1];
                }
            }
        }
        pu.redraw();
    };

    const extractKurotto = function() {
        return {height: getHeight(), width: getWidth(), numbers: extractNumbers()};
    };

    const displayKurottoSolution = function(response) {
        displayShading(response.shading);
    };

    const extractKuromasu = function() {
        return {height: getHeight(), width: getWidth(), numbers: extractNumbers()};
    };

    const displayKuromasuSolution = function(response) {
        displayShading(response.shading);
    };

    const extractYajikazu = function() {
        return {height: getHeight(), width: getWidth(), arrowNumbers: extractArrowNumbers()};
    };

    const displayYajikazuSolution = function(response) {
        displayShading(response.shading);
    };

    const extractShakashaka = function() {
        return {height: getHeight(), width: getWidth(), numbers: extractNumbers(), shading: extractShading()};
    };

    const displayShakashakaSolution = function(response) {
        displayTriangles(response.triangles);
    };

    const extractCanalView = function() {
        return {height: getHeight(), width: getWidth(), numbers: extractNumbers()}
    };

    const displayCanalViewSolution = function(response) {
        displayShading(response.shading);
    };

    const extractLookair = function() {
        return {height: getHeight(), width: getWidth(), numbers: extractNumbers()};
    };

    const displayLookairSolution = function(response) {
        displayShading(response.shading);
    };

    const extractJapaneseSums = function() {
        return {height: getHeight(), width: getWidth(), rows: extractOutsideLeftNumbers(), cols: extractOutsideTopNumbers(), n: extractJapaneseSumsN()};
    };

    const displayJapaneseSumsSolution = function(response) {
        displayShading(response.shading);
        displayNumbers(Object.fromEntries(Object.entries(response.numbers).filter(([k, v]) => v !== 0)));
    };

    const extractGuideArrow = function() {
        return {height: getHeight(), width: getWidth(), arrows: extractArrowShapes(), star: extractStarLocation()};
    };

    const displayGuideArrowSolution = function(response) {
        displayShading(response.shading);
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
                case 'kuromasu':
                    displayKuromasuSolution(response);
                    break;
                case 'yajikazu':
                    displayYajikazuSolution(response);
                    break;
                case 'shakashaka':
                    displayShakashakaSolution(response);
                    break;
                case 'lookair':
                    displayLookairSolution(response);
                    break;
                case 'canal':
                    displayCanalViewSolution(response);
                    break;
                case 'japanesesums':
                    displayJapaneseSumsSolution(response);
                    break;
                case 'guidearrow':
                    displayGuideArrowSolution(response);
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
                case 'kuromasu':
                    solverSocket.send(JSON.stringify({...extractKuromasu(), type}));
                    break;
                case 'yajikazu':
                    solverSocket.send(JSON.stringify({...extractYajikazu(), type}));
                    break;
                case 'shakashaka':
                    solverSocket.send(JSON.stringify({...extractShakashaka(), type}));
                    break;
                case 'lookair':
                    solverSocket.send(JSON.stringify({...extractLookair(), type}));
                    break;
                case 'canal':
                    solverSocket.send(JSON.stringify({...extractCanalView(), type}));
                    break;
                case 'japanesesums':
                    solverSocket.send(JSON.stringify({...extractJapaneseSums(), type}));
                    break;
                case 'guidearrow':
                    solverSocket.send(JSON.stringify({...extractGuideArrow(), type}));
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
