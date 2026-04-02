import json
import os

base_dir = "/apdcephfs/hunyuanaidjpsh2/jp_sh2_cephfs/apdcephfs_sh2/share_300000800/user/jackwkwang/code/OSWorld/evaluation_examples/examples/kdenlive"

tasks = [
    # Task 2-7: Apply Blur Effect to Video
    {
        "id": "9f99251e-6e8f-4ed2-8668-d2c48367e096",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/15368811_1920_1080_30fps.mp4', add it to the timeline, apply the 'Box Blur' (or 'Blur') video effect to the clip, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/15368811_1920_1080_30fps.mp4",
                            "path": "/home/user/Videos/15368811_1920_1080_30fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["box_blur", "boxblur", "blur", "avfilter.boxblur"],
                    "source_file": "15368811_1920_1080_30fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-8: Adjust Brightness and Contrast
    {
        "id": "42fad922-60c9-4f94-99db-1a78efe0ded7",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4', add it to the timeline, apply the 'Brightness' (or 'Brightness/Contrast') effect to the clip, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["brightness", "brightcontrast", "frei0r.brightness", "avfilter.eq"],
                    "source_file": "6533277-hd_1920_1080_24fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-9: Rotate Video Clip 90 Degrees
    {
        "id": "003b7be6-4535-4980-b603-c52292b79c6e",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4', add it to the timeline, apply the 'Rotate (keyframable)' or 'Transform' effect and rotate the clip 90 degrees clockwise, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_param",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["rotate", "affine", "qtblend", "avfilter.rotate"],
                    "param_name": "rotate",
                    "expected_value": 90,
                    "tolerance": 5
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-10: Crop Video (Zoom/Pan)
    {
        "id": "c37771a4-5bcc-4a3b-8afd-0f4257622f6c",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/14307439_1920_1080_60fps.mp4', add it to the timeline, apply the 'Crop, Scale and Tilt' (or 'Crop by Padding') effect to crop the video, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/14307439_1920_1080_60fps.mp4",
                            "path": "/home/user/Videos/14307439_1920_1080_60fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["crop", "qtcrop", "cropscale", "affine", "avfilter.crop"],
                    "source_file": "14307439_1920_1080_60fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-11: Apply Chroma Key (Green Screen) Effect
    {
        "id": "e34bd4c0-2af1-4405-9a7c-74e0668221b3",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4', add it to the timeline, apply the 'Chroma Key: Advanced' effect to the clip, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["frei0r.select0r", "chroma", "chroma_hold", "frei0r.bluescreen0r"],
                    "source_file": "6533277-hd_1920_1080_24fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-12: Add Audio Fade In and Fade Out
    {
        "id": "c8b836c8-45ff-471a-a2b4-4ae6b7f0c0e6",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Music/f88f7fdbb6b72e3fc1e2a10078b99b18.mp3', add it to the timeline on track A1, apply a 'Fade In' effect at the beginning (2 seconds) and a 'Fade Out' effect at the end (2 seconds), then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/f88f7fdbb6b72e3fc1e2a10078b99b18.mp3",
                            "path": "/home/user/Music/f88f7fdbb6b72e3fc1e2a10078b99b18.mp3"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_audio_fade",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "fade_in": True,
                    "fade_out": True,
                    "source_file": "f88f7fdbb6b72e3fc1e2a10078b99b18.mp3"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-13: Split/Cut a Clip on Timeline
    {
        "id": "8b5c202b-81ac-46b0-9f11-1af977f9656f",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/14307439_1920_1080_60fps.mp4', add it to the timeline on track V1, split the clip at the 5-second mark using the Razor tool so that it becomes two separate segments, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/14307439_1920_1080_60fps.mp4",
                            "path": "/home/user/Videos/14307439_1920_1080_60fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_clip_split",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "source_file": "14307439_1920_1080_60fps.mp4",
                    "min_segments": 2
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-14: Create Picture-in-Picture (PiP) Composition
    {
        "id": "5bd77807-0a8d-46cf-847d-c86b2c1b6447",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import two video files '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4' and '/home/user/Videos/15368811_1920_1080_30fps.mp4', place the first video on track V1 (main) and the second on track V2 (overlay), apply a 'Transform' or 'Position and Zoom' effect on the V2 clip to resize it to 1/4 of the screen and position it in the bottom-right corner, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        },
                        {
                            "local_path": "assets/kdenlive/15368811_1920_1080_30fps.mp4",
                            "path": "/home/user/Videos/15368811_1920_1080_30fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_multi_track_composition",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "main_file": "6533277-hd_1920_1080_24fps.mp4",
                    "overlay_file": "15368811_1920_1080_30fps.mp4",
                    "require_transform": True
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-15: Copy and Paste a Clip on Timeline
    {
        "id": "cdd648e0-4ab6-4391-af4d-5075eaceea81",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4', add it to the timeline on track V1, then copy the clip and paste it right after the original clip on the same track, so that the video plays twice consecutively, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_clip_count",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "source_file": "6533277-hd_1920_1080_24fps.mp4",
                    "min_count": 2
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-16: Group Clips on Timeline
    {
        "id": "383b7e01-d1e1-44ce-9eb4-ab50489a4235",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4' and '/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav', add the video to track V1 and the audio to track A1, select both clips and group them together, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        },
                        {
                            "local_path": "assets/kdenlive/mixkit-fast-rocket-whoosh-1714.wav",
                            "path": "/home/user/Music/mixkit-fast-rocket-whoosh-1714.wav"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_clip_group",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "min_groups": 1,
                    "min_clips_in_group": 2
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-17: Adjust Clip Opacity/Transparency
    {
        "id": "487c5d2e-b9bc-4d3f-871c-605414caf2ab",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/15368811_1920_1080_30fps.mp4', add it to the timeline, apply the 'Opacity' (or use the 'Transform' effect) and set the clip opacity to 50%, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/15368811_1920_1080_30fps.mp4",
                            "path": "/home/user/Videos/15368811_1920_1080_30fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_param",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["qtblend", "affine", "frei0r.transparency"],
                    "param_name": "opacity",
                    "expected_value": 0.5,
                    "tolerance": 0.1
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-18: Add Sepia Tone Effect
    {
        "id": "493e49e3-e76b-4505-bfb9-f93df341f9eb",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4', add it to the timeline, apply the 'Sepia' video effect to give the clip a vintage look, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["sepia", "tcolor", "frei0r.tint0r", "frei0r.colorize"],
                    "source_file": "6533277-hd_1920_1080_24fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-19: Mirror/Flip Video Horizontally
    {
        "id": "67890511-d1b9-4fd0-8a74-312e37bf5468",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/14307439_1920_1080_60fps.mp4', add it to the timeline, apply the 'Mirror' or 'Flip Horizontally' video effect to horizontally flip the video, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/14307439_1920_1080_60fps.mp4",
                            "path": "/home/user/Videos/14307439_1920_1080_60fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_effect_applied",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "effect_service": ["mirror", "avfilter.hflip", "frei0r.flippo"],
                    "source_file": "14307439_1920_1080_60fps.mp4"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-20: Add Wipe Transition Between Two Clips
    {
        "id": "7430eb95-0686-493a-9c54-828252af9512",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import two video files '/home/user/Videos/6533277-hd_1920_1080_24fps.mp4' and '/home/user/Videos/14307439_1920_1080_60fps.mp4', place them consecutively on the timeline, add a 'Wipe' transition between them, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/6533277-hd_1920_1080_24fps.mp4",
                            "path": "/home/user/Videos/6533277-hd_1920_1080_24fps.mp4"
                        },
                        {
                            "local_path": "assets/kdenlive/14307439_1920_1080_60fps.mp4",
                            "path": "/home/user/Videos/14307439_1920_1080_60fps.mp4"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_transition",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "transition_type": "composite"
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
    # Task 2-21: Add Image Watermark Overlay
    {
        "id": "2c5da2da-c708-4c09-a716-56e02e644793",
        "snapshot": "kdenlive",
        "instruction": "Open Kdenlive, import '/home/user/Videos/15368811_1920_1080_30fps.mp4' and an image file '/home/user/Pictures/watermark.png', place the video on track V1 and the image on track V2 as an overlay, apply a 'Composite' or 'Transform' effect on the image track to position it in the top-right corner, then save the project to '/home/user/Videos/project.kdenlive'.",
        "source": "",
        "config": [
            {
                "type": "upload_file",
                "parameters": {
                    "files": [
                        {
                            "local_path": "assets/kdenlive/15368811_1920_1080_30fps.mp4",
                            "path": "/home/user/Videos/15368811_1920_1080_30fps.mp4"
                        },
                        {
                            "local_path": "assets/kdenlive/watermark.png",
                            "path": "/home/user/Pictures/watermark.png"
                        }
                    ]
                }
            },
            {"type": "launch", "parameters": {"command": ["/home/user/.local/bin/kdenlive"]}},
            {"type": "sleep", "parameters": {"seconds": 3}}
        ],
        "trajectory": "trajectories/",
        "related_apps": ["kdenlive"],
        "evaluator": {
            "postconfig": [],
            "func": "check_kdenlive_multi_track_composition",
            "result": {
                "type": "vm_file",
                "path": "/home/user/Videos/project.kdenlive",
                "dest": "project.kdenlive"
            },
            "expected": {
                "type": "rule",
                "rules": {
                    "main_file": "15368811_1920_1080_30fps.mp4",
                    "overlay_file": "watermark.png",
                    "require_transform": True
                }
            }
        },
        "proxy": False,
        "fixed_ip": False,
        "possibility_of_env_change": "low"
    },
]

for task in tasks:
    filename = f"{task['id']}.json"
    filepath = os.path.join(base_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(task, f, indent=2, ensure_ascii=False)
    print(f"Created: {filename}")

print(f"\nTotal: {len(tasks)} L2 task files created.")
