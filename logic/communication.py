import json
import time

from utils import *

from ..core.GymEnvironment import EliminationEnv

error_map = ["RE", "TLE", "OLE"]
replay_file = "replay.json"
winner = 0
sleep_time = 0.3


def ai_communication(env: EliminationEnv, player, )


def read_human_information_and_apply(env: EliminationEnv, player, enemy_human):
    while 1:
        # 持续收消息
        ai_info = receive_ai_info()
        while ai_info["player"] != -1 and ai_info["player"] != player:
            ai_info = receive_ai_info()

        # 出现错误，退出游戏
        if ai_info["player"] == -1:
            write_end_info(replay_file, "player quit unexpectedly", 1-player)
            time.sleep(sleep_time)
            send_to_judger(
                (
                    replay_file,
                    "r").readlines()[-1].strip() + "\n").encode("utf-8")
            if enemy_human:
                # 如果对方是播放器，同时向对方转发结果
                # time.sleep(0.5)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    1 - player,
                )
            end_list = ["OK", "OK"]
            end_list[json.loads(ai_info["content"])["player"]] = error_map[
                json.loads(ai_info["content"])["error"]
            ]
            end_info = {
                "0": json.loads(ai_info["content"])["player"],
                "1": 1 - json.loads(ai_info["content"])["player"],
            }
            send_game_end_info(json.dumps(end_info), json.dumps(end_list))
            return False, ""

        if ai_info["content"] == "8\n":
            # 操作结束，停止接收消息
            command_list_str += "8\n"
            break
        elif ai_info["content"] == "9\n":
            gamestate.winner = 1 - player
            write_end_info(gamestate, "give up")
            time.sleep(sleep_time)
            send_to_judger(
                (
                    open(gamestate.replay_file,
                         "r").readlines()[-1].strip() + "\n"
                ).encode("utf-8"),
                player,
            )
            if enemy_human:
                # 如果对方是播放器，同时向对方转发结果
                # time.sleep(sleep_time)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    1 - player,
                )
            end_state = json.dumps(["OK", "OK"])
            end_info = {"0": 1 - gamestate.winner, "1": gamestate.winner}
            send_game_end_info(json.dumps(end_info), end_state)
            return False, ""
        elif ai_info["content"] == "10\n":
            gamestate.coin[player] += 999
        else:
            # 执行操作
            command = ai_info["content"][:-1].split()
            command = [int(i) for i in command]
            single_str = ""
            for i in command:
                single_str += str(i) + " "
            success = execute_single_command(
                player, gamestate, command[0], command[1:])
            if success:
                # 操作成功，返回操作结果
                command_list_str += single_str[:-1] + "\n"
                # time.sleep(0.5)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    player,
                )
                if enemy_human:
                    # 如果对方是播放器，同时向对方转发结果
                    # time.sleep(0.5)
                    send_to_judger(
                        (
                            open(gamestate.replay_file,
                                 "r").readlines()[-1].strip()
                            + "\n"
                        ).encode("utf-8"),
                        1 - player,
                    )
                # time.sleep(0.5)
                # 检查游戏是否结束，如果结束则停止操作
                gamestate.winner = is_game_over(gamestate)
                if gamestate.winner != -1:
                    break
            else:
                # 操作不成功，通知播放器
                # time.sleep(0.5)
                send_to_judger(
                    str(get_single_round_replay(gamestate, [], player, [-1])).encode(
                        "utf-8"
                    ),
                    player,
                )
                # time.sleep(0.5)

    # 玩家操作结束后，判断游戏是否结束
    if gamestate.winner != -1:
        write_end_info(gamestate, "game end normally")
        time.sleep(sleep_time)
        send_to_judger(
            (open(gamestate.replay_file, "r").readlines()[-1].strip() + "\n").encode(
                "utf-8"
            ),
            player,
        )
        if enemy_human:
            # time.sleep(0.5)
            # 如果对方是播放器，同时向对方转发结果
            send_to_judger(
                (
                    open(gamestate.replay_file,
                         "r").readlines()[-1].strip() + "\n"
                ).encode("utf-8"),
                1 - player,
            )
        # time.sleep(0.5)
        end_state = json.dumps(["OK", "OK"])
        end_info = {"0": 1 - gamestate.winner, "1": gamestate.winner}
        send_game_end_info(json.dumps(end_info), end_state)
        return False, ""

    if player == 0:
        # time.sleep(0.5)
        send_to_judger(
            (
                str(get_single_round_replay(gamestate, [], player, [8])).replace(
                    "'", '"'
                )
                + "\n"
            ).encode("utf-8"),
            player,
        )
        if enemy_human:
            # 如果对方是播放器，同时向对方转发结果
            # time.sleep(0.5)
            send_to_judger(
                (
                    str(get_single_round_replay(gamestate, [], player, [8])).replace(
                        "'", '"'
                    )
                    + "\n"
                ).encode("utf-8"),
                1 - player,
            )
        # time.sleep(0.5)
    else:
        # 如果是后手，更新回合
        update_round(gamestate)
        # 向播放器发送回合更新信息
        update_info = json.loads(
            open(gamestate.replay_file, "r").readlines()[-1].strip()
        )
        update_info["Player"] = player
        # time.sleep(0.5)
        send_to_judger(
            (str(update_info).replace("'", '"') + "\n").encode("utf-8"),
            player,
        )
        if enemy_human:
            # 如果对方是播放器，同时向对方转发结果
            # time.sleep(0.5)
            send_to_judger(
                (str(update_info).replace("'", '"') + "\n").encode("utf-8"),
                1 - player,
            )
        # time.sleep(0.5)
        # 判断游戏是否结束
        gamestate.winner = is_game_over(gamestate)
        if gamestate.winner != -1:
            write_end_info(gamestate, "game end normally")
            if enemy_human:
                time.sleep(sleep_time)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    player,
                )
            end_state = json.dumps(["OK", "OK"])
            end_info = {"0": 1 - gamestate.winner, "1": gamestate.winner}
            send_game_end_info(json.dumps(end_info), end_state)
            return False, ""
    return True, command_list_str


def read_ai_information_and_apply(gamestate: GameState, player, enemy_human):
    ai_info = receive_ai_info()
    while ai_info["player"] != -1 and ai_info["player"] != player:
        ai_info = receive_ai_info()
    if ai_info["player"] == -1:
        # 如果信息异常，胜负已分，游戏结束
        info = json.loads(ai_info["content"])
        gamestate.winner = 1 - info["player"]
        write_end_info(gamestate, "ai " +
                       str(info["player"]) + " quit unexpectedly")
        if enemy_human:
            time.sleep(sleep_time)
            send_to_judger(
                (
                    open(gamestate.replay_file,
                         "r").readlines()[-1].strip() + "\n"
                ).encode("utf-8"),
                player,
            )
        end_list = ["OK", "OK"]
        end_list[json.loads(ai_info["content"])["player"]] = error_map[
            json.loads(ai_info["content"])["error"]
        ]
        end_info = {
            "0": json.loads(ai_info["content"])["player"],
            "1": 1 - json.loads(ai_info["content"])["player"],
        }
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        return False, ""

    # 进行操作
    command_list_str = ai_info["content"]
    try:
        command_list = convert_command_list_str(command_list_str)
    except Exception:
        command_list_str = ai_info["content"]
        gamestate.winner = 1 - player
        write_end_info(gamestate, command_list_str)
        if enemy_human:
            time.sleep(sleep_time)
            send_to_judger(
                (
                    open(gamestate.replay_file,
                         "r").readlines()[-1].strip() + "\n"
                ).encode("utf-8"),
                player,
            )
        end_list = ["OK", "OK"]
        end_list[player] = "IA"
        end_info = {"0": player, "1": 1 - player}
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        return False, ""

    success = True
    command_list_str = ""
    for command in command_list:
        if command[0] == 8:
            command_list_str += "8\n"
            break
        if command[0] != 8:
            try:
                success = execute_single_command(
                    player, gamestate, command[0], command[1:]
                )
            except Exception:
                success = False
            # 如果操作失败，胜负已分
            if not success:
                gamestate.winner = 1 - player
                break
            # 如果对方是播放器，向对方发送操作结果
            single_str = ""
            for i in command:
                single_str += str(i) + " "
            command_list_str += single_str[:-1] + "\n"
            if enemy_human:
                time.sleep(sleep_time)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    1 - player,
                )
            # 如果满足条件，胜负已分
            gamestate.winner = is_game_over(gamestate)  # isgameover返回-1代表没结束
            if gamestate.winner != -1:
                break

    # 玩家0的操作回合结束后，判断游戏是否结束
    if gamestate.winner != -1:
        if success:
            write_end_info(gamestate, "game end normally")
        else:
            write_end_info(
                gamestate,
                "ai "
                + str(player)
                + " IA, operation "
                + ai_info["content"].replace("\n", "|"),
            )
        if enemy_human:
            time.sleep(sleep_time)
            send_to_judger(
                (
                    open(gamestate.replay_file,
                         "r").readlines()[-1].strip() + "\n"
                ).encode("utf-8"),
                1 - player,
            )
        end_list = ["OK", "OK"]
        if not success:
            end_list[player] = "IA"
        end_info = {"0": 1 - gamestate.winner, "1": gamestate.winner}
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        return False, ""

    # 发送正常回合消息
    # quit_running("before send round info")
    if player == 0:
        if enemy_human:
            # time.sleep(sleep_time)
            # 如果对方是播放器，同时向对方转发结果
            time.sleep(sleep_time)
            send_to_judger(
                (
                    str(get_single_round_replay(gamestate, [], player, [8])).replace(
                        "'", '"'
                    )
                    + "\n"
                ).encode("utf-8"),
                1 - player,
            )
    elif player == 1:
        update_round(gamestate)
        update_info = json.loads(
            open(gamestate.replay_file, "r").readlines()[-1].strip()
        )
        update_info["Player"] = player
        if enemy_human:
            # time.sleep(0.5)
            # 如果对方是播放器，同时向对方转发结果
            time.sleep(sleep_time)
            send_to_judger(
                (str(update_info).replace("'", '"') + "\n").encode("utf-8"),
                1 - player,
            )

        # 判断游戏是否结束
        gamestate.winner = is_game_over(gamestate)
        if gamestate.winner != -1:
            write_end_info(gamestate, "game end normally")
            if enemy_human:
                time.sleep(sleep_time)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    1 - player,
                )
            end_state = json.dumps(["OK", "OK"])
            end_info = {"0": 1 - gamestate.winner, "1": gamestate.winner}
            send_game_end_info(json.dumps(end_info), end_state)
            return False, ""

    return True, command_list_str


def count_surroundings(map, i, j, landtype):
    count = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            ni = i + dx
            nj = j + dy
            if ni >= 0 and ni < row and nj >= 0 and nj < col:
                if map[ni][nj].type in landtype:
                    count += 1
    return count


def update_map(gamestate: GameState):
    for row in gamestate.board:
        for cell in row:
            if cell.type == 2:
                sur_num = count_surroundings(
                    gamestate.board, cell.position[0], cell.position[1], [2]
                )
                if sur_num < 3:
                    cell.type = 0

    for row in gamestate.board:
        for cell in row:
            if cell.type in [0, 1]:
                sur_num = count_surroundings(
                    gamestate.board, cell.position[0], cell.position[1], [0, 1]
                )
                if sur_num < 4:
                    cell.type = 2


if __name__ == "__main__":
    import random
    import traceback

    try:
        # 接收judger的初始化信息
        init_info = receive_init_info()
        # 设置随机种子
        random.seed(init_info["config"]["random_seed"])

        gamestate = GameState()
        # 每局游戏唯一的游戏状态类，所有的修改应该在此对象中进行
        update_map(gamestate)
        init_generals(gamestate)
        gamestate.coin = [40, 40]

        gamestate.replay_file = init_info["replay"]
        player_type = init_info["player_list"]

        if player_type[0] == 0 or player_type[1] == 0:
            write_end_info(gamestate, "ai fail to start")
            if player_type[1] == 2:
                time.sleep(sleep_time)
                send_to_judger(
                    (
                        open(gamestate.replay_file,
                             "r").readlines()[-1].strip() + "\n"
                    ).encode("utf-8"),
                    1,
                )
            end_state = json.dumps(
                ["OK" if player_type[0] else "RE",
                    "OK" if player_type[1] else "RE"]
            )
            end_info = {
                "0": 1 if player_type[0] else 0,
                "1": 1 if player_type[1] else 0,
            }
            send_game_end_info(json.dumps(end_info), end_state)

        state = 0

        # 写入初始化json
        init_json = gamestate.trans_state_to_init_json(-1)
        init_json["Round"] = 0
        with open(gamestate.replay_file, "w") as f:
            f.write(str(init_json).replace("'", '"') + "\n")
        f.close()

        state += 1

        if player_type[0] == 1:
            send_round_config(1, 1024)
        elif player_type[0] == 2:
            send_round_config(180, 1024)

        # 向双方AI发送初始化信息
        json0 = gamestate.trans_state_to_init_json(0)
        json0["Round"] = 0
        json1 = gamestate.trans_state_to_init_json(1)
        json1["Round"] = 0
        send_round_info(
            state,
            [0],
            [0, 1],
            [
                str(json0).replace("'", '"') + "\n",
                str(json1).replace("'", '"') + "\n",
            ],
        )
        # state += 1

        player = 0
        game_continue = True
        while game_continue:
            # send_round_config(state, 1, 1024)
            if player_type[player] == 1:
                game_continue, operation_string = read_ai_information_and_apply(
                    gamestate, player, player_type[1 - player] == 2
                )
            elif player_type[player] == 2:
                game_continue, operation_string = read_human_information_and_apply(
                    gamestate, player, player_type[1 - player] == 2
                )

            if not game_continue:
                break
            player = 1 - player
            state += 1
            if player_type[player] == 1:
                send_round_config(1, 1024)
                send_round_info(
                    state,
                    [player],
                    [player],
                    [operation_string],
                )
            elif player_type[player] == 2:
                send_round_config(180, 1024)
                send_round_info(
                    state,
                    [player],
                    [],
                    [],
                )
    except Exception as e:
        errorFile = open(gamestate.replay_file, "a")
        errorFile.write(traceback.format_exc())
        errorFile.close()
        quit_running("")
