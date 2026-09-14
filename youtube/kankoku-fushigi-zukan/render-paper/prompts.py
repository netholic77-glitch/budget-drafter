# -*- coding: utf-8 -*-
"""EP.01 景福宮 — 장면별 이미지 생성 프롬프트.
레퍼런스(로우폴리 페이퍼크래프트)의 질감·팔레트·광원을 고정 접미사로 강제한다."""

SUFFIX = (
    "Handmade low-poly papercraft diorama, photographed as a miniature tabletop set. "
    "Folded matte cardstock with visible flat facets and crisp fold edges, no gloss. "
    "Warm paper palette: cream, ivory, sand, terracotta, salmon, muted rose, deep navy, mustard. "
    "Soft diffused daylight from the upper left, gentle long soft shadows on a pale paper floor. "
    "Clean flat color-block paper panels as the backdrop. Shallow depth of field. "
    "Simple stylised paper figures with rounded faceted heads, small dot eyes, no detailed faces. "
    "Vertical 9:16 composition, figures in the lower half, generous empty space in the bottom third. "
    "No text, no letters, no numbers, no logos, no watermark."
)

SCENES = {
 "c01_hook": "A single paper figure traveller in a terracotta top and navy trousers stands before a large "
             "two-tier Korean palace gate made of folded paper, dark navy tiled roof with upturned eaves, "
             "deep red-brown walls, a navy beam band under the roof, a dark doorway in the centre. The figure looks up.",
 "c02_founding": "Two paper figures building a Korean palace hall out of paper; one raises both arms, one carries a "
                 "paper plank. A neat stack of pale wooden paper planks sits to the right. Half-finished hall behind.",
 "c03_fire": "A collapsed Korean tiled roof made of dark brown folded paper lying broken on a pale floor, a lone dark "
             "paper figure standing before it with arms raised. Small square paper embers float in the air. "
             "Backdrop panels in burnt orange and deep red.",
 "c04_empty": "An empty lot: nine flat round pale-grey paper foundation stones set in the ground, small folded green "
              "paper weeds between them, one small paper figure standing far to the right looking at the emptiness.",
 "c05_move": "Two paper figures carrying a red paper palanquin with a small navy tiled roof on a long pale pole "
             "between them, walking right. A smaller Korean palace roof sits in the distance. Dusk-toned backdrop panels.",
 "c07_rebuild": "A rebuilding site: a tall pale paper crane frame with a round pulley, a rope lowering a block of stone, "
                "two paper figures working, a Korean palace hall behind them.",
 "c08_lost": "A wide empty pale stone platform of folded paper with only six low round foundation stones left on top, "
             "no building. One grey paper figure standing in front. Pale washed-out grey-white backdrop, misty.",
 "c09_restore": "A Korean palace hall wrapped in a lattice of pale wooden paper scaffolding poles, two paper figures "
                "in mustard and terracotta working at its base.",
 "c11_today": "Two paper figures wearing Korean hanbok made of folded paper, one in red and pink, one in navy and blue, "
              "standing in front of a restored two-tier Korean palace hall on a bright day.",
}
