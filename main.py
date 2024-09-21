import json
import random
import time

from core.GymEnvironment import EliminationEnv
from logic.utils import *

ERROR_MAP = ["RE", "TLE", "OLE"]
replay_file = None


def interact(env: EliminationEnv, player, enemy_type, self_type):
    '''
    env: 游戏逻辑维护的唯一局面
    player: 目前进行操作的玩家
    enemy_type player_type: 0为ai 1为播放器
    
    输入当前局面 输出要转发给对方的字符串
    '''
    # 收消息
    ai_info = receive_ai_info()
    while ai_info["player"] != -1 and ai_info["player"] != player:
        ai_info = receive_ai_info()
    # 判定交互对象状态
    # 如果交互对象异常则退出
    if ai_info["player"] == -1:
        return_dict = env.render()
        error_info = json.loads(ai_info["content"])
        error_type = error_info['error']
        error_player = error_info['player']
        return_dict["StopReason"] = f"Unexpected behavior of player {error_player}, judger returned error type {ERROR_MAP[error_type]}."

        # 回放文件写入结束信息
        replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

        if self_type == 2:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player
            )

        if enemy_type == 2:
            send_to_judger(
                json.dumps(new_state, ensure_ascii=False).encode("utf-8"), 1 - player
            )

        end_list = ["OK", "OK"]
        end_list[json.loads(ai_info["content"])["player"]] = ERROR_MAP[
            json.loads(ai_info["content"])["error"]
        ]
        end_info = {
            "0": json.loads(ai_info["content"])["player"],
            "1": 1 - json.loads(ai_info["content"])["player"],
        }
        send_game_end_info(json.dumps(end_info), json.dumps(end_list))
        replay_file.close()
        exit()

        # 对方AI则直接结束，对方播放器则转发结束信息
        if enemy_type == 2:
            return False, return_dict
        return False, None
    else:
        # 获取操作
        action = [int(i) for i in ai_info["content"].split(" ")]
        # 进行操作
        try:
            # 操作成功
            env.step(action, player=player)
        except:
            error = traceback.format_exc()
            return_dict = env.render()
            return_dict["StopReason"] = f"Invalid Operation from player {player}, judger returned error {error}."
            # 回放文件写入结束信息
            replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

            if self_type == 2:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), player
                )

            if enemy_type == 2:
                send_to_judger(
                    json.dumps(new_state, ensure_ascii=False).encode("utf-8"),
                    1 - player,
                )

            end_state = ["OK", "OK"]
            end_state[player] = "IA"
            send_game_end_info(json.dumps(
                {"0": player, "1": 1-player}), end_state)
            replay_file.close()
            exit()


        new_state = env.render()
        replay_file.write(json.dumps(new_state, ensure_ascii=False)+"\n")

        if self_type == 2:
            send_to_judger(
                json.dumps(new_state, ensure_ascii=False).encode("utf-8"), player
            )

        if new_state['steps']:
            if enemy_type == 1:
                return True, str(action)
            elif enemy_type == 2:
                return True, json.dumps(new_state, ensure_ascii=False)
        else:
            if enemy_type == 1:
                return False, str(action)
            elif enemy_type == 2:
                return False, json.dumps(new_state, ensure_ascii=False)


if __name__ == "__main__":
    import traceback

    try:
        # 接收judger的初始化信息
        init_info = receive_init_info()
        replay_file = open(init_info["replay"], 'w')
        # 设置随机种子
        try:
            seed = init_info["config"]["random_seed"]
        except:
            seed = random.randint(1, 100000000)

        env = EliminationEnv('logic')
        env.reset(seed=seed)
        # 每局游戏唯一的游戏状态类，所有的修改应该在此对象中进行

        player_type = init_info["player_list"]

        if player_type[0] == 0 or player_type[1] == 0:
            end_dict = env.render()
            end_dict["StopReason"] = "player quit unexpectedly"
            end_json = json.dumps(end_dict, ensure_ascii=False)
            replay_file.write(end_json + "\n")

            if player_type[1] == 2:
                send_to_judger(json.dumps(end_dict), 1)

            if player_type[0] == 2:
                send_to_judger(json.dumps(end_dict), 0)

            end_state = json.dumps(
                ["OK" if player_type[0] else "RE",
                    "OK" if player_type[1] else "RE"]
            )
            end_info = {
                "0": 1 if player_type[0] else 0,
                "1": 1 if player_type[1] else 0,
            }
            send_game_end_info(json.dumps(end_info), end_state)
            replay_file.close()
            exit()

        state = 0

        # 写入初始化json
        init_json = json.dumps(env.render(), ensure_ascii=False)
        replay_file.write(init_json+'\n')

        state += 1

        if player_type[0] == 1:
            send_round_config(2, 1024)
        elif player_type[0] == 2:
            send_round_config(60, 1024)

        # 向双方AI发送初始化信息
        send_round_info(
            state,
            [0],
            [0, 1],
            [
                str(seed) if player_type[0] == 1 else init_json,
                str(seed) if player_type[1] == 1 else init_json,
            ],
        )

        player = 0
        game_continue = True
        while game_continue:
            # send_round_config(state, 1, 1024)
            game_continue, info = interact(
                env, player, player_type[1 - player], player_type[player]
            )

            if not game_continue:
                break

            player = 1 - player
            state += 1
            if player_type[player] == 1:
                send_round_config(1, 1024)
            elif player_type[player] == 2:
                send_round_config(60, 1024)
            send_round_info(
                state,
                [player],
                [player],
                [info],
            )

        end_state = json.dumps(
            ["OK", "OK"]
        )
        winner = 0 if env._score[0] > env._score[1] else 1
        end_json = env.render()
        end_json["StopReason"] = f"player {winner} wins."
        end_info = {
            "0": 1-winner,
            "1": winner,
        }

        if player_type[0] == 2:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 0)
        if player_type[1] == 2:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 1)

        replay_file.write(json.dumps(end_json, ensure_ascii=False) + "\n")
        send_game_end_info(json.dumps(end_info), end_state)
        replay_file.close()
        exit()

    except Exception as e:
        replay_file.write(traceback.format_exc())
        replay_file.write(str(e))
        replay_file.close()
        quit_running()

    replay_file.close()
