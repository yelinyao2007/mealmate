"""
Demo data for the MealMate multi-agent system.
Provides high-quality, realistic Chinese meal planning data as fallback
when the LLM API is unavailable or returns errors.

The data is parameterized by season and adapts to input parameters.
"""
import json
import random
import re
from typing import Dict, Any, List


def _build_menu(season: str, budget: float, dietary: List[str]) -> dict:
    """Generate a realistic weekly menu adapted to season and constraints."""

    seasonal_menus = {
        "春季": {
            "周一": {
                "午餐": {
                    "主食": ["米饭", "花卷"],
                    "荤菜": ["红烧鸡腿", "青椒肉丝"],
                    "素菜": ["清炒菠菜", "香菇油菜"],
                    "汤品": "番茄蛋花汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["二米饭（大米+小米）"],
                    "荤菜": ["清蒸鲈鱼"],
                    "素菜": ["蒜蓉西兰花", "凉拌莴笋"],
                    "汤品": "紫菜虾皮汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周二": {
                "午餐": {
                    "主食": ["米饭", "馒头"],
                    "荤菜": ["宫保鸡丁", "番茄炒蛋"],
                    "素菜": ["蚝油生菜", "素炒豆芽"],
                    "汤品": "冬瓜排骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["杂粮粥", "玉米饼"],
                    "荤菜": ["红烧肉末豆腐"],
                    "素菜": ["清炒空心菜", "醋溜白菜"],
                    "汤品": "丝瓜鸡蛋汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周三": {
                "午餐": {
                    "主食": ["米饭", "南瓜发糕"],
                    "荤菜": ["糖醋里脊", "韭菜炒虾仁"],
                    "素菜": ["香干芹菜", "清炒时蔬"],
                    "汤品": "山药排骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["红豆粥", "花卷"],
                    "荤菜": ["葱烧海参豆腐"],
                    "素菜": ["蒜蓉菠菜", "凉拌黄瓜"],
                    "汤品": "西红柿豆腐汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周四": {
                "午餐": {
                    "主食": ["米饭", "豆沙包"],
                    "荤菜": ["黄焖鸡", "鱼香肉丝"],
                    "素菜": ["干煸四季豆", "清炒莲藕"],
                    "汤品": "玉米鸡汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["小米粥", "蒸饺"],
                    "荤菜": ["清蒸鸡翅"],
                    "素菜": ["蒜蓉茄子", "炒莴笋丝"],
                    "汤品": "菠菜蛋花汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周五": {
                "午餐": {
                    "主食": ["米饭", "花生酱花卷"],
                    "荤菜": ["可乐鸡翅", "木须肉"],
                    "素菜": ["香菇青菜", "凉拌三丝"],
                    "汤品": "莲藕猪骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["八宝粥"],
                    "荤菜": ["清蒸鳊鱼"],
                    "素菜": ["清炒荷兰豆", "拍黄瓜"],
                    "汤品": "银耳红枣汤",
                    "estimated_cost_per_person": budget
                }
            }
        },
        "夏季": {
            "周一": {
                "午餐": {
                    "主食": ["米饭", "绿豆糕"],
                    "荤菜": ["柠檬鸡丝", "番茄炒蛋"],
                    "素菜": ["凉拌黄瓜", "蒜蓉空心菜"],
                    "汤品": "绿豆百合汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["绿豆粥", "凉面"],
                    "荤菜": ["白切鸡"],
                    "素菜": ["凉拌苦瓜", "拍黄瓜"],
                    "汤品": "冬瓜薏米汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周二": {
                "午餐": {
                    "主食": ["米饭", "馒头"],
                    "荤菜": ["清蒸鲈鱼", "丝瓜炒虾仁"],
                    "素菜": ["凉拌木耳", "清炒丝瓜"],
                    "汤品": "番茄蛋花汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["小米粥", "葱油饼"],
                    "荤菜": ["酸汤肥牛"],
                    "素菜": ["蒜泥茄子", "炒豆角"],
                    "汤品": "紫菜蛋花汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周三": {
                "午餐": {
                    "主食": ["米饭", "玉米"],
                    "荤菜": ["蒜香排骨", "青椒炒肉"],
                    "素菜": ["清炒苋菜", "凉拌豆皮"],
                    "汤品": "冬瓜排骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["杂粮粥", "花卷"],
                    "荤菜": ["红烧豆腐鱼"],
                    "素菜": ["清炒西葫芦", "糖拌番茄"],
                    "汤品": "丝瓜蛋汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周四": {
                "午餐": {
                    "主食": ["米饭", "南瓜饼"],
                    "荤菜": ["咖喱鸡块", "番茄炒牛肉"],
                    "素菜": ["蒜蓉秋葵", "清炒莲藕"],
                    "汤品": "酸梅汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["红豆薏米粥"],
                    "荤菜": ["葱油鲫鱼"],
                    "素菜": ["凉拌三丝", "清炒毛豆"],
                    "汤品": "银耳莲子汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周五": {
                "午餐": {
                    "主食": ["米饭", "花卷"],
                    "荤菜": ["糖醋小排", "虾仁滑蛋"],
                    "素菜": ["凉拌海带丝", "蒜蓉油麦菜"],
                    "汤品": "莲子银耳汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["皮蛋瘦肉粥"],
                    "荤菜": ["清蒸鲳鱼"],
                    "素菜": ["凉拌莴笋", "炒苦瓜"],
                    "汤品": "绿豆汤",
                    "estimated_cost_per_person": budget
                }
            }
        },
        "秋季": {
            "周一": {
                "午餐": {
                    "主食": ["米饭", "南瓜发糕"],
                    "荤菜": ["板栗烧鸡", "番茄炒蛋"],
                    "素菜": ["清炒西兰花", "醋溜土豆丝"],
                    "汤品": "银耳雪梨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["小米南瓜粥"],
                    "荤菜": ["红烧带鱼"],
                    "素菜": ["蒜蓉菠菜", "拌三丝"],
                    "汤品": "山药排骨汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周二": {
                "午餐": {
                    "主食": ["米饭", "芋头饼"],
                    "荤菜": ["红烧肉", "芹菜炒虾仁"],
                    "素菜": ["香菇油菜", "凉拌莲藕"],
                    "汤品": "莲藕花生汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["杂粮粥", "馒头"],
                    "荤菜": ["清蒸鲫鱼"],
                    "素菜": ["蒜蓉秋葵", "炒白菜"],
                    "汤品": "紫菜蛋花汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周三": {
                "午餐": {
                    "主食": ["米饭", "玉米窝头"],
                    "荤菜": ["黄焖鸡", "鱼香肉丝"],
                    "素菜": ["干煸四季豆", "素炒豆芽"],
                    "汤品": "玉米排骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["红薯粥", "花卷"],
                    "荤菜": ["茄汁大虾"],
                    "素菜": ["清炒莴笋", "凉拌木耳"],
                    "汤品": "冬瓜虾皮汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周四": {
                "午餐": {
                    "主食": ["米饭", "红薯"],
                    "荤菜": ["宫保鸡丁", "木须肉"],
                    "素菜": ["蚝油生菜", "清炒山药"],
                    "汤品": "番茄牛肉汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["八宝粥", "葱花饼"],
                    "荤菜": ["红烧鲤鱼"],
                    "素菜": ["清炒南瓜", "蒜泥白菜"],
                    "汤品": "丝瓜鸡蛋汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周五": {
                "午餐": {
                    "主食": ["米饭", "菊花糕"],
                    "荤菜": ["糖醋里脊", "虾仁豆腐"],
                    "素菜": ["香干炒芹菜", "凉拌三丝"],
                    "汤品": "银耳枸杞汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["山药薏米粥"],
                    "荤菜": ["清蒸鳊鱼"],
                    "素菜": ["蒜蓉茄子", "醋溜白菜"],
                    "汤品": "百合莲子汤",
                    "estimated_cost_per_person": budget
                }
            }
        },
        "冬季": {
            "周一": {
                "午餐": {
                    "主食": ["米饭", "花卷"],
                    "荤菜": ["萝卜炖牛腩", "番茄炒蛋"],
                    "素菜": ["清炒大白菜", "香菇油菜"],
                    "汤品": "羊肉萝卜汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["玉米糁粥", "馒头"],
                    "荤菜": ["红烧带鱼"],
                    "素菜": ["蒜蓉菠菜", "酸辣土豆丝"],
                    "汤品": "山药枸杞汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周二": {
                "午餐": {
                    "主食": ["米饭", "豆沙包"],
                    "荤菜": ["红烧鸡块", "鱼香肉丝"],
                    "素菜": ["蒜苗炒腊肉", "清炒莲藕"],
                    "汤品": "当归鸡汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["红枣小米粥", "韭菜盒子"],
                    "荤菜": ["白菜豆腐炖肉"],
                    "素菜": ["素炒白萝卜", "凉拌菠菜"],
                    "汤品": "番茄蛋花汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周三": {
                "午餐": {
                    "主食": ["米饭", "窝窝头"],
                    "荤菜": ["黄焖鸡", "酱爆鱿鱼"],
                    "素菜": ["干煸花菜", "蚝油生菜"],
                    "汤品": "排骨莲藕汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["杂粮粥", "花卷"],
                    "荤菜": ["清蒸鲈鱼"],
                    "素菜": ["蒜蓉西兰花", "凉拌金针菇"],
                    "汤品": "冬瓜虾皮汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周四": {
                "午餐": {
                    "主食": ["米饭", "南瓜饼"],
                    "荤菜": ["宫保鸡丁", "木须肉"],
                    "素菜": ["清炒芥蓝", "醋溜白菜"],
                    "汤品": "玉米排骨汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["腊八粥"],
                    "荤菜": ["红烧猪蹄"],
                    "素菜": ["蒜蓉茄子", "炒土豆丝"],
                    "汤品": "银耳红枣汤",
                    "estimated_cost_per_person": budget
                }
            },
            "周五": {
                "午餐": {
                    "主食": ["米饭", "肉包子"],
                    "荤菜": ["糖醋排骨", "青椒炒肉"],
                    "素菜": ["香干芹菜", "清炒大白菜"],
                    "汤品": "萝卜羊肉汤",
                    "estimated_cost_per_person": budget
                },
                "晚餐": {
                    "主食": ["红豆粥", "花卷"],
                    "荤菜": ["清蒸鳊鱼"],
                    "素菜": ["蒜蓉菠菜", "凉拌三丝"],
                    "汤品": "当归黄芪汤",
                    "estimated_cost_per_person": budget
                }
            }
        }
    }

    # Fallback to spring if season not recognized
    menu = seasonal_menus.get(season, seasonal_menus["春季"])

    seasonal_highlights_map = {
        "春季": ["春笋", "菠菜", "荠菜", "韭菜", "莴笋"],
        "夏季": ["丝瓜", "苦瓜", "黄瓜", "空心菜", "秋葵"],
        "秋季": ["南瓜", "山药", "莲藕", "板栗", "芋头"],
        "冬季": ["白萝卜", "大白菜", "菠菜", "莲藕", "山药"],
    }

    dietary_note = ""
    if dietary:
        dietary_note = f"本菜单已针对以下饮食需求进行调整：{'、'.join(dietary)}。"

    return {
        "weekly_menu": menu,
        "total_weekly_cost_per_person": budget * 10,
        "nutrition_summary": f"本周菜单注重营养均衡，每日膳食包含优质蛋白质、新鲜蔬菜和适量主食。"
                            f"蛋白质来源多样化（鸡、鱼、猪肉、豆制品），蔬菜以当季时令为主。{dietary_note}",
        "seasonal_highlights": seasonal_highlights_map.get(season, seasonal_highlights_map["春季"]),
        "special_notes": "菜品以软烂易消化为主，适合老年人食用；汤品每日更换，兼顾滋补与清淡。"
    }


def _build_nutrition(menu_data: dict) -> dict:
    """Generate realistic nutrition analysis for a menu."""
    days = ["周一", "周二", "周三", "周四", "周五"]
    daily = {}
    scores = []
    for day in days:
        score = random.randint(80, 95)
        scores.append(score)
        calories = random.randint(1600, 2000)
        daily[day] = {
            "score": score,
            "calories_estimate": f"约{calories}kcal",
            "protein_adequate": True,
            "fiber_adequate": score > 82,
            "issues": [],
            "suggestions": []
        }
        if score < 85:
            daily[day]["issues"].append("膳食纤维摄入略显不足，建议增加杂粮和蔬菜比例")
            daily[day]["suggestions"].append("可将部分精白米饭替换为糙米或燕麦")
        if calories < 1700:
            daily[day]["issues"].append("总热量偏低，可能不能满足部分体力活动者需求")
            daily[day]["suggestions"].append("适当增加主食份量或添加坚果类零食")
        if not daily[day]["issues"]:
            daily[day]["issues"].append("营养搭配良好，荤素比例合理")
        if not daily[day]["suggestions"]:
            daily[day]["suggestions"].append("可适当增加奶制品，补充钙质")

    overall = int(sum(scores) / len(scores))
    elderly_score = max(overall - random.randint(0, 5), 75)

    return {
        "overall_score": overall,
        "daily_analysis": daily,
        "weekly_summary": {
            "strengths": [
                "蛋白质来源多样化（禽肉、鱼类、猪肉、豆制品），营养全面",
                "每日均有绿叶蔬菜，维生素和矿物质摄入充足",
                "汤品搭配合理，有助于老年人消化吸收",
                "主食品种多样，粗细搭配得当"
            ],
            "weaknesses": [
                "奶制品出现频率较低，钙质摄入可能不足",
                "水果供应未在菜单中体现，建议餐后补充时令水果"
            ],
            "missing_nutrients": [
                "钙（建议增加牛奶、豆腐摄入）",
                "维生素D（建议适当户外活动）",
                "膳食纤维（部分日期偏低）"
            ],
            "improvement_suggestions": [
                "每日增加一份牛奶或酸奶（200ml），改善钙摄入",
                "午餐后提供时令水果，补充维生素C",
                "每周安排1-2次粗粮主食日（如糙米饭、全麦馒头）",
                "适当增加深色蔬菜比例，提升微量元素摄入"
            ]
        },
        "elderly_friendly_score": elderly_score,
        "elderly_notes": "菜品整体偏软烂，适合老年人食用。建议关注以下几点："
                        "1）每餐盐分控制在3g以内；2）鱼类去骨处理；"
                        "3）蔬菜切碎或煮软；4）汤品不宜过油过咸。"
    }


def _build_procurement(menu_data: dict, num_people: int) -> dict:
    """Generate realistic procurement list."""
    factor = num_people / 50.0  # scale from base 50 people

    def _scale(base_kg: float) -> str:
        val = round(base_kg * factor, 1)
        return f"{val}kg"

    def _price(base_price: float) -> float:
        return round(base_price * factor, 1)

    procurement = {
        "肉类": [
            {"name": "猪瘦肉", "quantity": _scale(12), "unit_price": 28.0, "total_price": _price(336.0), "shelf_life_days": 3, "priority": "high"},
            {"name": "鸡腿/鸡翅", "quantity": _scale(10), "unit_price": 22.0, "total_price": _price(220.0), "shelf_life_days": 2, "priority": "high"},
            {"name": "鲈鱼/鳊鱼", "quantity": _scale(8), "unit_price": 35.0, "total_price": _price(280.0), "shelf_life_days": 1, "priority": "high"},
            {"name": "排骨", "quantity": _scale(6), "unit_price": 38.0, "total_price": _price(228.0), "shelf_life_days": 2, "priority": "high"},
            {"name": "虾仁", "quantity": _scale(4), "unit_price": 55.0, "total_price": _price(220.0), "shelf_life_days": 1, "priority": "high"},
        ],
        "蔬菜": [
            {"name": "菠菜", "quantity": _scale(6), "unit_price": 6.0, "total_price": _price(36.0), "shelf_life_days": 2, "priority": "high"},
            {"name": "西兰花", "quantity": _scale(5), "unit_price": 8.0, "total_price": _price(40.0), "shelf_life_days": 3, "priority": "medium"},
            {"name": "番茄", "quantity": _scale(8), "unit_price": 5.0, "total_price": _price(40.0), "shelf_life_days": 4, "priority": "medium"},
            {"name": "黄瓜", "quantity": _scale(5), "unit_price": 4.0, "total_price": _price(20.0), "shelf_life_days": 3, "priority": "medium"},
            {"name": "油菜/生菜", "quantity": _scale(6), "unit_price": 5.0, "total_price": _price(30.0), "shelf_life_days": 2, "priority": "high"},
            {"name": "莴笋", "quantity": _scale(4), "unit_price": 5.5, "total_price": _price(22.0), "shelf_life_days": 4, "priority": "low"},
            {"name": "芹菜", "quantity": _scale(3), "unit_price": 6.0, "total_price": _price(18.0), "shelf_life_days": 3, "priority": "medium"},
            {"name": "冬瓜", "quantity": _scale(5), "unit_price": 3.0, "total_price": _price(15.0), "shelf_life_days": 7, "priority": "low"},
        ],
        "主食/粮油": [
            {"name": "大米", "quantity": _scale(25), "unit_price": 5.5, "total_price": _price(137.5), "shelf_life_days": 90, "priority": "low"},
            {"name": "面粉", "quantity": _scale(8), "unit_price": 4.5, "total_price": _price(36.0), "shelf_life_days": 60, "priority": "low"},
            {"name": "小米", "quantity": _scale(3), "unit_price": 9.0, "total_price": _price(27.0), "shelf_life_days": 60, "priority": "low"},
            {"name": "食用油", "quantity": _scale(5), "unit_price": 12.0, "total_price": _price(60.0), "shelf_life_days": 180, "priority": "low"},
            {"name": "杂粮（红豆、绿豆、薏米）", "quantity": _scale(3), "unit_price": 12.0, "total_price": _price(36.0), "shelf_life_days": 90, "priority": "low"},
        ],
        "调味料": [
            {"name": "生抽/老抽", "quantity": "2瓶", "unit_price": 15.0, "total_price": 30.0, "shelf_life_days": 365, "priority": "low"},
            {"name": "食盐", "quantity": "2包", "unit_price": 3.0, "total_price": 6.0, "shelf_life_days": 365, "priority": "low"},
            {"name": "白糖", "quantity": "1包", "unit_price": 8.0, "total_price": 8.0, "shelf_life_days": 365, "priority": "low"},
            {"name": "醋", "quantity": "1瓶", "unit_price": 10.0, "total_price": 10.0, "shelf_life_days": 365, "priority": "low"},
            {"name": "蒜/姜/葱", "quantity": _scale(2), "unit_price": 10.0, "total_price": _price(20.0), "shelf_life_days": 7, "priority": "medium"},
        ],
        "豆制品/蛋类": [
            {"name": "鸡蛋", "quantity": f"{int(150 * factor)}个", "unit_price": 0.8, "total_price": _price(120.0), "shelf_life_days": 14, "priority": "medium"},
            {"name": "豆腐", "quantity": _scale(6), "unit_price": 6.0, "total_price": _price(36.0), "shelf_life_days": 2, "priority": "high"},
            {"name": "香干/千张", "quantity": _scale(3), "unit_price": 10.0, "total_price": _price(30.0), "shelf_life_days": 3, "priority": "medium"},
        ],
        "其他": [
            {"name": "紫菜/虾皮", "quantity": "各2包", "unit_price": 12.0, "total_price": 24.0, "shelf_life_days": 180, "priority": "low"},
            {"name": "银耳/红枣/枸杞", "quantity": "各1包", "unit_price": 15.0, "total_price": 45.0, "shelf_life_days": 90, "priority": "low"},
            {"name": "香菇（干）", "quantity": "2包", "unit_price": 18.0, "total_price": 36.0, "shelf_life_days": 180, "priority": "low"},
        ]
    }

    total = sum(
        item["total_price"]
        for cat in procurement.values()
        for item in cat
    )

    return {
        "procurement_list": procurement,
        "total_budget": round(total, 1),
        "budget_per_person_per_day": round(total / num_people / 5, 1),
        "perishable_items": ["鲈鱼/鳊鱼（当日采购）", "虾仁（当日采购）", "菠菜（2日内使用）",
                             "豆腐（2日内使用）", "鸡腿/鸡翅（2日内使用）"],
        "storage_notes": "1）肉类和海鲜分装冷冻保存，每日提前解冻；"
                        "2）叶菜类用保鲜膜包裹冷藏，不超过2天；"
                        "3）根茎类蔬菜阴凉通风处存放；"
                        "4）调味料密封防潮保存。",
        "suggested_suppliers": "建议联系龙华街道定点供应商采购，优先选择本地农贸市场时令蔬菜；"
                              "肉类和海鲜建议从正规批发市场进货，确保检疫合格。",
        "waste_reduction_tips": [
            "按周分批采购蔬菜，避免一次性采购过多导致腐烂",
            "鱼虾等海鲜当日采购当日使用，保证新鲜",
            "建立库存台账，先进先出原则使用食材",
            "剩余食材及时加工成半成品冷冻保存",
            "与供应商协商小批量多频次配送模式"
        ]
    }


def _build_customization(menu_data: dict, target_groups: List[str]) -> dict:
    """Generate realistic meal customization for special populations."""
    days = ["周一", "周二", "周三", "周四", "周五"]

    plans = []
    added_types = set()  # Track which plan types we've already added
    for group in target_groups:
        if ("老" in group or "elderly" in group.lower()) and "elderly" not in added_types:
            added_types.add("elderly")
            daily = {}
            for day in days:
                daily[day] = {
                    "午餐": {
                        "主食": "软烂米饭（小份）",
                        "菜品": ["清蒸肉饼（免咀嚼负担）", "蒜蓉菠菜（切碎）", "蒸蛋羹"],
                        "注意事项": "减盐30%，食材切碎或炖烂，避免过硬食物"
                    },
                    "晚餐": {
                        "主食": "小米粥（软糯）",
                        "菜品": ["清蒸鱼（去骨）", "炖烂白菜豆腐"],
                        "注意事项": "晚餐宜清淡，控制油盐，避免胀气食物"
                    }
                }
            plans.append({
                "target_group": "青年白领",
                "modifications": "1）所有菜品减盐30%，减油20%；2）肉类切碎或做成肉饼/肉糜；"
                                "3）鱼类必须去骨；4）蔬菜切碎煮软；5）主食以软烂粥饭为主；"
                                "6）增加蒸蛋、豆腐等软质高蛋白食物",
                "daily_plans": daily,
                "nutrition_notes": "每日蛋白质≥50g，钙≥800mg，膳食纤维≥20g。"
                                  "建议每日补充1杯牛奶或酸奶。少食多餐，每餐七分饱。",
                "preparation_tips": "1）提前将肉类解冻切碎；2）蔬菜先焯水再烹饪缩短加热时间；"
                                   "3）使用不粘锅减少用油量；4）粥类提前1小时熬制确保软糯。"
            })

        if ("糖尿病" in group or "diabetes" in group.lower()) and "diabetes" not in added_types:
            added_types.add("diabetes")
            daily = {}
            for day in days:
                daily[day] = {
                    "午餐": {
                        "主食": "杂粮饭（糙米+燕麦，控量150g）",
                        "菜品": ["清蒸鸡胸肉", "清炒苦瓜", "凉拌木耳"],
                        "注意事项": "严格控制碳水总量，主食不超过150g，选用低GI食材"
                    },
                    "晚餐": {
                        "主食": "荞麦面（小份100g）",
                        "菜品": ["清蒸鱼", "蒜蓉西兰花"],
                        "注意事项": "晚餐碳水减半，增加蔬菜比例，餐后2小时监测血糖"
                    }
                }
            plans.append({
                "target_group": "糖尿病患者",
                "modifications": "1）主食替换为低GI杂粮（糙米、燕麦、荞麦）；"
                                "2）每餐碳水化合物控制在40-50g；3）增加蔬菜比例至50%以上；"
                                "4）避免含糖调味料；5）烹饪方式以蒸煮为主，避免油炸",
                "daily_plans": daily,
                "nutrition_notes": "每日碳水化合物总量控制在200-250g，蛋白质≥60g。"
                                  "推荐少食多餐（3正餐+2-3加餐），每餐定时定量。",
                "preparation_tips": "1）杂粮提前浸泡2小时便于蒸煮；2）避免用淀粉勾芡；"
                                   "3）调味以醋、姜、蒜为主，减少糖和蚝油使用。"
            })

        if ("高血压" in group or "hypertension" in group.lower()) and "hypertension" not in added_types:
            added_types.add("hypertension")
            daily = {}
            for day in days:
                daily[day] = {
                    "午餐": {
                        "主食": "米饭（适量）",
                        "菜品": ["清蒸鸡肉", "芹菜拌花生", "清炒丝瓜"],
                        "注意事项": "全天盐分控制在5g以内，多选高钾蔬菜（芹菜、菠菜）"
                    },
                    "晚餐": {
                        "主食": "杂粮粥",
                        "菜品": ["清蒸鱼", "凉拌海带丝"],
                        "注意事项": "晚餐清淡为主，避免腌制食品和加工肉类"
                    }
                }
            plans.append({
                "target_group": "高血压患者",
                "modifications": "1）全天食盐控制在5g以内（老年人3-4g）；2）禁用腌制食品和加工肉类；"
                                "3）增加高钾食物（香蕉、菠菜、芹菜）；4）减少动物脂肪摄入；"
                                "5）汤品不加盐或极少盐",
                "daily_plans": daily,
                "nutrition_notes": "钠摄入<2000mg/天，钾摄入>3500mg/天。"
                                  "增加膳食纤维摄入，适量补充钙和镁。",
                "preparation_tips": "1）使用限盐勺精确控制用盐量；2）多用天然调味料（醋、姜、蒜、柠檬）替代盐；"
                                   "3）汤品最后调味，减少盐分溶入。"
            })

    # If no specific groups matched, add a generic elderly plan
    if not plans:
        plans.append({
            "target_group": "社区老年居民",
            "modifications": "减盐减油，食材软烂处理，增加蒸煮类菜品比例",
            "daily_plans": {day: {
                "午餐": {"主食": "软烂米饭", "菜品": ["清蒸肉饼", "蒜蓉蔬菜", "蒸蛋"], "注意事项": "减盐减油"},
                "晚餐": {"主食": "杂粮粥", "菜品": ["清蒸鱼（去骨）", "炖烂蔬菜"], "注意事项": "清淡为主"}
            } for day in days},
            "nutrition_notes": "保证每日蛋白质≥50g，钙≥800mg。建议配合每日一杯牛奶。",
            "preparation_tips": "肉类切碎煮烂，蔬菜切细，鱼类去骨。"
        })

    return {
        "customized_plans": plans,
        "delivery_suggestions": "1）使用保温餐盒配送，确保送达温度≥60°C；"
                               "2）独居老人送餐时顺便确认老人身体状况；"
                               "3）餐盒标注菜品名称和注意事项（如'低盐''去骨鱼'）；"
                               "4）建立送餐反馈机制，及时调整口味偏好。",
        "safety_reminders": [
            "严格区分普通餐和特殊饮食餐，防止混淆",
            "糖尿病患者餐食单独标注碳水含量",
            "高血压患者餐食标注'限盐'标识",
            "过敏体质者需提前登记过敏原，配餐时严格排除",
            "送餐人员需接受基本食品安全培训"
        ]
    }


def _build_agent1_response(messages: list) -> str:
    """Generate a demo recipe for Agent 1 (Direct Chef). Returns formatted text, not dict."""
    recipe_text = """**🍳 Quick Garlic Butter Pasta**
⏱ Prep: 5 min | Cook: 15 min | Total: 20 min
Difficulty: Easy

**Ingredients:**
- 200g spaghetti
- 4 cloves garlic, minced
- 3 tbsp butter
- 2 tbsp olive oil
- 1/4 cup grated parmesan
- Fresh parsley, chopped
- Salt and pepper to taste
- Red pepper flakes (optional)

**Steps:**
1. Cook pasta in salted boiling water until al dente (about 8-10 minutes). Reserve 1/2 cup pasta water before draining.
2. While pasta cooks, heat olive oil and butter in a large pan over medium heat.
3. Add minced garlic and cook for 1-2 minutes until fragrant and just golden — don't burn it!
4. Toss drained pasta into the garlic butter. Add a splash of pasta water to create a silky sauce.
5. Remove from heat, toss with parmesan, parsley, salt, and pepper.
6. Plate it up and hit it with more parmesan and red pepper flakes if you're feeling spicy.

**💡 Tip:** The secret is that starchy pasta water — it emulsifies the butter into a creamy sauce without any cream!

```json
{"title":"Quick Garlic Butter Pasta","description":"A simple, soul-satisfying pasta that comes together in 20 minutes with pantry staples.","ingredients":[{"item":"spaghetti","qty":"200","unit":"g"},{"item":"garlic","qty":"4","unit":"cloves"},{"item":"butter","qty":"3","unit":"tbsp"},{"item":"olive oil","qty":"2","unit":"tbsp"},{"item":"parmesan","qty":"1/4","unit":"cup"},{"item":"parsley","qty":"to taste","unit":""},{"item":"salt and pepper","qty":"to taste","unit":""},{"item":"red pepper flakes","qty":"optional","unit":""}],"steps":["Cook pasta in salted boiling water until al dente (about 8-10 minutes). Reserve 1/2 cup pasta water before draining.","While pasta cooks, heat olive oil and butter in a large pan over medium heat.","Add minced garlic and cook for 1-2 minutes until fragrant and just golden.","Toss drained pasta into the garlic butter. Add a splash of pasta water to create a silky sauce.","Remove from heat, toss with parmesan, parsley, salt, and pepper.","Plate it up and hit it with more parmesan and red pepper flakes if you're feeling spicy."],"prep_minutes":5,"cook_minutes":15,"difficulty":"Easy","tip":"The secret is that starchy pasta water — it emulsifies the butter into a creamy sauce without any cream!"}
```"""
    return recipe_text


def _build_agent2_response(messages: list) -> dict:
    """Generate a demo analysis for Agent 2 (Social Vision)."""
    return {
        "recipe_title": "Golden Garlic Butter Pasta",
        "description": "A simple, soul-satisfying pasta that comes together in 20 minutes with pantry staples.",
        "ingredients": [
            {"item": "spaghetti", "qty": "200", "unit": "g"},
            {"item": "garlic", "qty": "4", "unit": "cloves"},
            {"item": "butter", "qty": "3", "unit": "tbsp"},
            {"item": "olive oil", "qty": "2", "unit": "tbsp"},
            {"item": "parmesan", "qty": "1/4", "unit": "cup"},
            {"item": "parsley", "qty": "handful", "unit": ""},
        ],
        "steps": [
            "Boil spaghetti in salted water until al dente. Reserve pasta water.",
            "Melt butter with olive oil in a large pan over medium heat.",
            "Saute garlic until fragrant and golden (1-2 min).",
            "Toss pasta into the pan, add splash of pasta water.",
            "Finish with parmesan and parsley. Serve immediately."
        ],
        "preference_tags": ["comfort-food", "quick-meal", "budget-friendly", "weeknight-dinner"],
        "auto_comment": "This looks amazing! The golden garlic butter sauce with perfectly al dente pasta — chef's kiss. I'd add a squeeze of lemon to brighten it up!",
        "confidence": "high",
        "memory_update": "Enjoys simple Italian-style pasta dishes; appreciates quick weeknight meals with minimal ingredients"
    }


def _build_agent3_response(messages: list) -> dict:
    """Generate a demo weekly plan for Agent 3 (Weekly Planner)."""
    return {
        "weekly_plan": {
            "monday": {"meal": "Garlic Butter Pasta with Side Salad", "is_new_suggestion": False},
            "tuesday": {"meal": "Lemon Herb Salmon with Roasted Broccoli", "is_new_suggestion": False},
            "wednesday": {"meal": "Ginger Soy Tofu Stir-Fry with Rice", "is_new_suggestion": False},
            "thursday": {"meal": "Chicken Fajita Bowl with Avocado", "is_new_suggestion": True},
            "friday": {"meal": "Shrimp Fried Rice with Vegetables", "is_new_suggestion": True},
            "saturday": {"meal": "Homemade Margherita Pizza", "is_new_suggestion": True},
            "sunday": {"meal": "Slow Cooker Beef Stew with Crusty Bread", "is_new_suggestion": True}
        },
        "grocery_list": {
            "produce": [
                {"item": "broccoli", "qty": 2, "unit": "heads", "est_price": 3.00},
                {"item": "avocado", "qty": 2, "unit": "whole", "est_price": 3.00},
                {"item": "lemon", "qty": 3, "unit": "whole", "est_price": 1.50},
                {"item": "ginger", "qty": 1, "unit": "knob", "est_price": 1.00},
                {"item": "bell peppers", "qty": 3, "unit": "whole", "est_price": 3.00},
                {"item": "mixed salad greens", "qty": 1, "unit": "bag", "est_price": 3.50},
                {"item": "onion", "qty": 2, "unit": "whole", "est_price": 1.00},
                {"item": "carrots", "qty": 4, "unit": "whole", "est_price": 1.50},
                {"item": "potatoes", "qty": 3, "unit": "whole", "est_price": 2.00}
            ],
            "dairy": [
                {"item": "parmesan cheese", "qty": 1, "unit": "block", "est_price": 5.00},
                {"item": "mozzarella", "qty": 1, "unit": "ball", "est_price": 4.00},
                {"item": "butter", "qty": 1, "unit": "stick", "est_price": 3.00}
            ],
            "meat": [
                {"item": "salmon fillets", "qty": 2, "unit": "pieces", "est_price": 12.00},
                {"item": "chicken breast", "qty": 1, "unit": "lb", "est_price": 6.00},
                {"item": "shrimp", "qty": 0.5, "unit": "lb", "est_price": 7.00},
                {"item": "beef stew meat", "qty": 1, "unit": "lb", "est_price": 8.00}
            ],
            "pantry": [
                {"item": "spaghetti", "qty": 1, "unit": "box", "est_price": 2.00},
                {"item": "rice", "qty": 1, "unit": "bag", "est_price": 3.50},
                {"item": "soy sauce", "qty": 1, "unit": "bottle", "est_price": 3.00},
                {"item": "pizza dough", "qty": 1, "unit": "ball", "est_price": 3.00},
                {"item": "canned tomatoes", "qty": 2, "unit": "cans", "est_price": 3.00}
            ],
            "other": [
                {"item": "firm tofu", "qty": 1, "unit": "block", "est_price": 2.50},
                {"item": "crusty bread", "qty": 1, "unit": "loaf", "est_price": 4.00}
            ]
        },
        "total_estimated_cost": 86.50,
        "estimated_restaurant_cost": 210.00,
        "estimated_savings": 123.50,
        "savings_tip": "Buy the whole salmon fillet instead of pre-cut portions — it's about 30% cheaper per pound, and you can portion it yourself in 2 minutes!"
    }


def detect_agent_type(messages: list) -> str:
    """Detect which agent is calling based on system prompt content."""
    if not messages:
        return "unknown"
    system_msg = ""
    for m in messages:
        if m.get("role") == "system":
            system_msg = m.get("content", "")
            break
    system_msg_lower = system_msg.lower()

    # Check for ProfileAgent (user health profile analysis)
    if "健康营养顾问" in system_msg or "profile agent" in system_msg_lower:
        return "profile_agent"

    # Check for MealMate AI Chef (conversational recipe chat)
    if "mealmate" in system_msg_lower and ("ai 大厨" in system_msg_lower or "ai chef" in system_msg_lower or "冰箱里" in system_msg):
        return "agent1_direct_chef"
    
    # New agent types (young person's AI fridge manager)
    if "weekly meal planning" in system_msg_lower or "7-day meal plan" in system_msg_lower:
        return "agent3_weekly_planner"
    if "culinary ai assistant" in system_msg_lower or "home cook" in system_msg_lower or "available ingredients" in system_msg_lower:
        return "agent1_direct_chef"
    if "food vision" in system_msg_lower or "reverse-engineer" in system_msg_lower or "social ai assistant" in system_msg_lower:
        return "agent2_social_vision"

    # Legacy agent types (elderly meal service)
    if "智膳大厨" in system_msg or "菜单规划" in system_msg:
        return "menu_planner"
    elif "营养师" in system_msg or "营养均衡" in system_msg:
        return "nutrition_analyzer"
    elif "采购" in system_msg:
        return "procurement"
    elif "膳食定制" in system_msg or "特殊人群" in system_msg:
        return "meal_customizer"
    return "unknown"


def extract_params_from_messages(messages: list) -> dict:
    """Extract parameters from user message content."""
    user_msg = ""
    for m in messages:
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    params = {}

    # Extract season
    for s in ["春季", "夏季", "秋季", "冬季"]:
        if s in user_msg:
            params["season"] = s
            break
    if "season" not in params:
        params["season"] = "春季"

    # Extract budget
    budget_match = re.search(r"预算[：:]\s*(\d+)", user_msg)
    if budget_match:
        params["budget"] = float(budget_match.group(1))
    else:
        params["budget"] = 15.0

    # Extract num_people
    people_match = re.search(r"(\d+)\s*人", user_msg)
    if people_match:
        params["num_people"] = int(people_match.group(1))
    else:
        params["num_people"] = 50

    # Extract dietary requirements
    params["dietary"] = []
    for d in ["低盐", "低脂", "低糖", "高蛋白", "清真", "素食"]:
        if d in user_msg:
            params["dietary"].append(d)

    # Extract target groups
    params["target_groups"] = []
    for g in ["青年白领", "健身爱好者", "素食主义者", "加班族", "学生党", "新手厨师", "家庭煮夫"]:
        if g in user_msg:
            params["target_groups"].append(g)
    if not params["target_groups"]:
        params["target_groups"] = ["青年白领"]

    return params


def _build_profile_analysis(messages: list) -> dict:
    """Generate a realistic profile analysis response."""
    user_msg = ""
    for m in messages:
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    height_match = re.search(r"身高[：:]\s*(\d+\.?\d*)", user_msg)
    weight_match = re.search(r"体重[：:]\s*(\d+\.?\d*)", user_msg)
    age_match = re.search(r"年龄[：:]\s*(\d+)", user_msg)

    height = float(height_match.group(1)) if height_match else 170
    weight = float(weight_match.group(1)) if weight_match else 65
    age = int(age_match.group(1)) if age_match else 28
    bmi = round(weight / ((height / 100) ** 2), 1)

    if bmi < 18.5:
        bmi_category = "偏瘦"
    elif bmi < 24:
        bmi_category = "正常"
    elif bmi < 28:
        bmi_category = "偏胖"
    else:
        bmi_category = "肥胖"

    goal = ""
    if "减脂" in user_msg or "lose_fat" in user_msg:
        goal = "减脂"
        recommended_calories = max(1500, int((weight * 22) - 300))
        calorie_deficit = 300
        macro_targets = {"protein_g": int(weight * 2.0), "fat_g": 50, "carbs_g": int(recommended_calories * 0.4 / 4), "fiber_g": 30}
        key_principles = [
            "控制总热量摄入，每日热量缺口300-500千卡",
            "增加蛋白质摄入至" + str(macro_targets["protein_g"]) + "g/天，保护肌肉不流失",
            "减少精制碳水和添加糖，多选择全谷物和蔬菜",
            "每周进行3-5次有氧运动，每次30-45分钟",
        ]
    elif "增肌" in user_msg or "gain_muscle" in user_msg:
        goal = "增肌"
        recommended_calories = int(weight * 30 + 300)
        calorie_deficit = 0
        macro_targets = {"protein_g": int(weight * 2.2), "fat_g": 65, "carbs_g": int(recommended_calories * 0.45 / 4), "fiber_g": 30}
        key_principles = [
            "保证热量盈余300-500千卡，支持肌肉合成",
            "每日蛋白质摄入" + str(macro_targets["protein_g"]) + "g，均匀分配到每餐",
            "配合力量训练，每周4-5次，确保蛋白质利用效率",
            "碳水化合物集中在训练前后摄入",
        ]
    elif "控糖" in user_msg or "sugar_control" in user_msg:
        goal = "控糖"
        recommended_calories = max(1500, int(weight * 25))
        calorie_deficit = 0
        macro_targets = {"protein_g": int(weight * 1.5), "fat_g": 55, "carbs_g": int(recommended_calories * 0.35 / 4), "fiber_g": 35}
        key_principles = [
            "选择低GI食材，避免血糖剧烈波动",
            "每餐碳水控制在40-50g，少食多餐",
            "增加膳食纤维至35g/天，延缓糖分吸收",
            "餐后30分钟轻度运动，有助于血糖控制",
        ]
    else:
        goal = "一般健康"
        recommended_calories = int(weight * 28)
        calorie_deficit = 0
        macro_targets = {"protein_g": int(weight * 1.2), "fat_g": 60, "carbs_g": int(recommended_calories * 0.5 / 4), "fiber_g": 25}
        key_principles = [
            "均衡营养，五谷为养，五果为助",
            "肉类选择去肥瘦肉，鱼类每周2-3次",
            "每日蔬菜500g以上，水果200-300g",
            "保持规律作息，每周适量运动",
        ]

    health_warnings = []
    if "高血压" in user_msg or "hypertension" in user_msg:
        health_warnings.append("注意低盐饮食，每日食盐不超过5g")
        health_warnings.append("避免腌制食品和加工肉类")
    if "糖尿病" in user_msg or "diabetes" in user_msg:
        health_warnings.append("严格控制碳水化合物摄入，选择低GI食物")
        health_warnings.append("餐后2小时监测血糖，保持血糖稳定")

    return {
        "bmi": bmi,
        "bmi_category": bmi_category,
        "recommended_calories": recommended_calories,
        "macro_targets": macro_targets,
        "goal_analysis": {
            "goal": goal,
            "calorie_deficit": calorie_deficit,
            "expected_weekly_loss_kg": round(calorie_deficit * 7 / 7700, 1) if calorie_deficit > 0 else 0,
            "key_principles": key_principles,
        },
        "health_warnings": health_warnings if health_warnings else ["暂无特殊健康预警，保持良好生活习惯"],
        "weekly_core_principles": [
            f"每日摄入{recommended_calories}千卡",
            f"蛋白质占比{round(macro_targets['protein_g'] * 4 / recommended_calories * 100)}%",
            "多食用全谷物和新鲜蔬菜",
            "控制加工食品和添加糖的摄入",
        ],
        "summary": f"根据你的BMI {bmi}（{bmi_category}范围），建议每日摄入{recommended_calories}千卡，蛋白质{macro_targets['protein_g']}g，脂肪{macro_targets['fat_g']}g，碳水化合物{macro_targets['carbs_g']}g。目标为{goal}，请结合运动实现最佳效果。",
    }


def generate_demo_response(messages: list) -> str:
    """Generate a demo response based on the detected agent type and parameters."""
    agent_type = detect_agent_type(messages)
    params = extract_params_from_messages(messages)

    # New agent types
    if agent_type == "agent1_direct_chef":
        # Agent 1 returns formatted text directly, not JSON
        return _build_agent1_response(messages)
    elif agent_type == "agent2_social_vision":
        data = _build_agent2_response(messages)
    elif agent_type == "agent3_weekly_planner":
        data = _build_agent3_response(messages)
    elif agent_type == "profile_agent":
        data = _build_profile_analysis(messages)
    # Legacy agent types
    elif agent_type == "menu_planner":
        data = _build_menu(params["season"], params["budget"], params["dietary"])
    elif agent_type == "nutrition_analyzer":
        data = _build_nutrition({})
    elif agent_type == "procurement":
        data = _build_procurement({}, params["num_people"])
    elif agent_type == "meal_customizer":
        data = _build_customization({}, params["target_groups"])
    else:
        # Generic response
        data = {"message": "Demo mode - agent type not recognized", "status": "ok"}

    return json.dumps(data, ensure_ascii=False, indent=2)
