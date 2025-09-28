import json
import random
import time

from core.GymEnvironment import EliminationEnv
from logic.utils import *
from core.gamedata import *

ERROR_MAP = ["RE", "TLE", "OLE"]
replay_file = None

class Player():
    def __init__(
        self,
        id,
        type,
    ):
        self.id = id
        self.action = []
        self.type = type

def interact(env: EliminationEnv, self_player, enemy_player):
    '''
    env: 游戏逻辑维护的唯一局面
    self_player: 当前玩家
    enemy_player: 对手玩家
    
    输入当前局面 输出要转发给对方的字符串
    '''
    # 收消息
    ai_info = receive_ai_info()
    while ai_info["player"] != -1 and ai_info["player"] != self_player.id:
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

        if self_player.type == Type.PLAYER:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), self_player.id
            )

        if enemy_player.type == Type.PLAYER:
            send_to_judger(
                json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), enemy_player.id
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
        time.sleep(0.5)
        exit(0)
    else:
        try:
            # 获取操作
            info = json.loads(ai_info["content"])
            action = info["action"]
            skill = info["skill"] % 3
            # 进行操作
            env.step(env.coord_to_num(action), skill=skill, player=player)
        except:
            error = traceback.format_exc()
            return_dict = env.render()
            return_dict["StopReason"] = (
                f"Invalid Operation {ai_info['content']} from player {player}, judger returned error {error}."
            )
            # 回放文件写入结束信息
            replay_file.write(json.dumps(return_dict, ensure_ascii=False)+"\n")

            if self_player.type == Type.PLAYER:
                send_to_judger(
                    json.dumps(return_dict, ensure_ascii=False).encode("utf-8"), self_player.id
                )

            if enemy_player.type == Type.PLAYER:
                send_to_judger(
                    json.dumps(new_state, ensure_ascii=False).encode("utf-8"), enemy_player.id,
                )

            end_state = ["OK", "OK"]
            end_state[self_player.id] = "IA"
            send_game_end_info(
                json.dumps({"0": self_player.id, "1": enemy_player.id}), json.dumps(end_state)
            )
            replay_file.close()
            time.sleep(0.5)
            exit(0)

        new_state = env.render()
        replay_file.write(json.dumps(new_state, ensure_ascii=False)+"\n")

        if self_player.type == 2:
            send_to_judger(
                json.dumps(new_state, ensure_ascii=False).encode("utf-8"), player
            )

        if new_state['steps']:
            if enemy_player.type == 1:
                return True, f"{action[0]} {action[1]} {action[2]} {action[3]}\n"
            elif enemy_player.type == 2:
                return True, json.dumps(new_state, ensure_ascii=False)
        else:
            if enemy_player.type == 1:
                return False, None
            elif enemy_player.type == 2:
                return False, None


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
        
        players = [Player(0,init_info["player_list"][0]),Player(1,init_info["player_list"][1])]

        if players[0].type == 0 or players[1].type == 0:
            end_dict = env.render()
            end_dict["StopReason"] = "player quit unexpectedly"
            end_json = json.dumps(end_dict, ensure_ascii=False)
            replay_file.write(end_json + "\n")

            if players[0].type == 2:
                send_to_judger(json.dumps(end_dict), 0)

            if players[1].type == 2:
                send_to_judger(json.dumps(end_dict), 1)

            end_state = json.dumps(
                ["OK" if players[0].type else "RE",
                    "OK" if players[1].type else "RE"]
            )
            end_info = {
                "0": 1 if players[0].type else 0,
                "1": 1 if players[1].type else 0,
            }
            send_game_end_info(json.dumps(end_info), end_state)
            replay_file.close()
            time.sleep(1)
            exit(0)

        state = 0

        # 写入初始化json
        init_json = json.dumps(env.render(), ensure_ascii=False)
        replay_file.write(init_json+'\n')

        state += 1

        if players[0].type == 1:
            send_round_config(2, 1024)
        elif players[0].type == 2:
            send_round_config(60, 1024)

        # 向双方AI发送初始化信息
        send_round_info(
            state,
            [0],
            [0, 1],
            [
                f"{seed} 0\n" if players[0].type == 1 else init_json,
                f"{seed} 1\n" if players[1].type == 1 else init_json,
            ],
        )

        player = 0
        game_continue = True
        while game_continue:
            # send_round_config(state, 1, 1024)
            game_continue, info = interact(
                env, player, players[1 - player].type, players[player].type
            )

            if not game_continue:
                break

            player = 1 - player
            state += 1
            if players[player].type == 1:
                send_round_config(1, 1024)
            elif players[player].type == 2:
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

        if players[0].type == 2:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 0)
        if players[1].type == 2:
            send_to_judger(json.dumps(end_json, ensure_ascii=False).encode("utf-8"), 1)

        replay_file.write(json.dumps(end_json, ensure_ascii=False) + "\n")
        send_game_end_info(json.dumps(end_info), end_state)
        replay_file.close()
        time.sleep(1)
        exit(0)

    except Exception as e:
        replay_file.write(traceback.format_exc())
        replay_file.write(str(e))
        replay_file.close()
        quit_running()

    replay_file.close()
