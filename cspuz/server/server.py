import asyncio
import json
import sys
import websockets

from cspuz.puzzle import kurotto

def serialize_puzzle_info(puzzle_info):
    json_data = {'type': puzzle_info['type'], 'height': puzzle_info['height'], 'width': puzzle_info['width']}
    for name in puzzle_info:
        if name not in ['type', 'height', 'width']:
            json_data[name] = {str(k): v for k, v in puzzle_info.get(name, {}).items()}
    return json.dumps(json_data)

def deserialize_puzzle_info(message):
    json_data = json.loads(message)
    puzzle_info = {'type': json_data['type'], 'height': json_data['height'], 'width': json_data['width']}
    for name in json_data:
        if name not in ['type', 'height', 'width']:
            puzzle_info[name] = {eval(k): v for k, v in json_data.get(name, {}).items()}
    return puzzle_info

def parse_kurotto(puzzle_info):
    height, width = puzzle_info['height'], puzzle_info['width']
    problem_data = [[-2 for _ in range(width)] for _ in range(height)]
    for (y, x), val in puzzle_info['numbers'].items():
        problem_data[y][x] = -1 if val == '' else int(val)
    return height, width, problem_data

def impossible_shading(height, width):
    shading = {}
    for y in range(height):
        for x in range(width):
            shading[(y, x)] = (True if (x + y) % 2 == 0 else False)
    return shading

def shading_from_sat(height, width, is_black):
    shading = {}
    for y in range(height):
        for x in range(width):
            if is_black[y, x].sol is None:
                shading[(y, x)] = None
            else:
                shading[(y, x)] = is_black[y, x].sol
    return shading

async def echo(websocket):
    async for message in websocket:

        try:
            puzzle_info = deserialize_puzzle_info(message)

            if puzzle_info['type'] == 'kurotto':
                height, width, problem_data = parse_kurotto(puzzle_info)
                is_sat, is_black = kurotto.solve_kurotto(height, width, problem_data)
                if is_sat:
                    await websocket.send(serialize_puzzle_info({'type': 'kurotto', 'height': height, 'width': width, 'shading': shading_from_sat(height, width, is_black)}))
                else:
                    await websocket.send(serialize_puzzle_info({'type': 'kurotto', 'height': height, 'width': width, 'shading': impossible_shading(height, width)}))

            else:
                print(f"Unknown puzzle type {puzzle_info['type']}", file=sys.stderr)
                await websocket.send(json.dumps({'type': 'error'}))

        except Exception as e:
            print("Failed to handle message", file=sys.stderr)
            print(message, file=sys.stderr)
            print(e, file=sys.stderr)
            await websocket.send(json.dumps({'type': 'error'}))            


async def main():
    async with websockets.serve(echo, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())
