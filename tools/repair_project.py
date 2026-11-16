from pathlib import Path
import json
import re
import sys

root = Path(sys.argv[1])

def write(rel, value):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value, encoding="utf-8", newline="\n")

# Remove the throwables that the user asked to exclude.
remove = [
    "src/main/java/com/blenderphysics/entity/FluidBombEntity.java",
    "src/main/java/com/blenderphysics/item/FluidBombItem.java",
    "src/client/java/com/blenderphysics/client/FluidBombEntityRenderer.java",
    "src/main/resources/assets/blenderphysics/models/item/water_bomb.json",
    "src/main/resources/assets/blenderphysics/models/item/lava_bomb.json",
    "src/main/resources/assets/blenderphysics/models/item/slime_bomb.json",
    "src/main/resources/data/blenderphysics/recipes/water_bomb.json",
    "src/main/resources/data/blenderphysics/recipes/lava_bomb.json",
    "src/main/resources/data/blenderphysics/recipes/slime_bomb.json",
    "src/main/resources/assets/blenderphysics/textures/item/water_bomb.png",
    "src/main/resources/assets/blenderphysics/textures/item/lava_bomb.png",
    "src/main/resources/assets/blenderphysics/textures/item/slime_bomb.png",
]
for rel in remove:
    p = root / rel
    if p.exists():
        p.unlink()

write("src/main/java/com/blenderphysics/registry/ModEntities.java", """package com.blenderphysics.registry;

import com.blenderphysics.BlenderPhysicsMod;
import com.blenderphysics.entity.PhysicsRigidBodyEntity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

public final class ModEntities {
    public static EntityType<PhysicsRigidBodyEntity> PHYSICS_RIGID_BODY;

    private ModEntities() {}

    public static void register() {
        PHYSICS_RIGID_BODY = Registry.register(Registries.ENTITY_TYPE,
                Identifier.of(BlenderPhysicsMod.MOD_ID, "physics_rigid_body"),
                EntityType.Builder.<PhysicsRigidBodyEntity>create(PhysicsRigidBodyEntity::new, SpawnGroup.MISC)
                        .dimensions(EntityDimensions.fixed(1.0f, 1.0f))
                        .maxTrackingRange(64)
                        .trackingTickInterval(2)
                        .build());
    }
}
""")

write("src/main/java/com/blenderphysics/registry/ModItems.java", """package com.blenderphysics.registry;

import com.blenderphysics.BlenderPhysicsMod;
import com.blenderphysics.item.RealisticFluidBucketItem;
import com.blenderphysics.item.RealityWandItem;
import com.blenderphysics.physics.FluidType;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.Identifier;

public final class ModItems {
    public static Item REALITY_WAND;
    public static Item REALISTIC_WATER_BUCKET;
    public static Item REALISTIC_LAVA_BUCKET;
    public static Item REALISTIC_SLIME_BUCKET;
    public static Item WATER_EMITTER_ITEM;
    public static Item LAVA_EMITTER_ITEM;
    public static Item SLIME_EMITTER_ITEM;
    public static Item FLUID_DRAIN_ITEM;

    private ModItems() {}

    private static Item register(String name, Item item) {
        return Registry.register(Registries.ITEM, Identifier.of(BlenderPhysicsMod.MOD_ID, name), item);
    }

    public static void register() {
        REALITY_WAND = register("reality_wand",
                new RealityWandItem(new Item.Settings().maxCount(1)));
        REALISTIC_WATER_BUCKET = register("realistic_water_bucket",
                new RealisticFluidBucketItem(FluidType.WATER, new Item.Settings().maxCount(1)));
        REALISTIC_LAVA_BUCKET = register("realistic_lava_bucket",
                new RealisticFluidBucketItem(FluidType.LAVA, new Item.Settings().maxCount(1)));
        REALISTIC_SLIME_BUCKET = register("realistic_slime_bucket",
                new RealisticFluidBucketItem(FluidType.SLIME, new Item.Settings().maxCount(1)));
        WATER_EMITTER_ITEM = register("water_emitter", new BlockItem(ModBlocks.WATER_EMITTER, new Item.Settings()));
        LAVA_EMITTER_ITEM = register("lava_emitter", new BlockItem(ModBlocks.LAVA_EMITTER, new Item.Settings()));
        SLIME_EMITTER_ITEM = register("slime_emitter", new BlockItem(ModBlocks.SLIME_EMITTER, new Item.Settings()));
        FLUID_DRAIN_ITEM = register("fluid_drain", new BlockItem(ModBlocks.FLUID_DRAIN, new Item.Settings()));
    }
}
""")

p = root / "src/main/java/com/blenderphysics/registry/ModItemGroups.java"
s = p.read_text(encoding="utf-8")
s = re.sub(r"\n\s*entries\.add\(ModItems\.(?:WATER_BOMB|LAVA_BOMB|SLIME_BOMB)\);", "", s)
p.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/client/java/com/blenderphysics/client/BlenderPhysicsClientMod.java"
s = p.read_text(encoding="utf-8")
s = re.sub(r"\n\s*EntityRendererRegistry\.register\(ModEntities\.(?:WATER_BOMB_ENTITY|LAVA_BOMB_ENTITY|SLIME_BOMB_ENTITY),[^\n]*\);", "", s)
p.write_text(s, encoding="utf-8", newline="\n")

def patch_use(rel):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    sig = re.compile(
        r"@Override\s+public\s+(?:net\.minecraft\.util\.)?(?:ActionResult|TypedActionResult\s*<\s*(?:net\.minecraft\.item\.)?ItemStack\s*>)\s+use\s*\(World\s+world,\s*PlayerEntity\s+user,\s*Hand\s+hand\)\s*\{"
    )
    m = sig.search(s)
    if not m:
        raise RuntimeError("use() signature not found: " + rel)
    opening = s.find("{", m.start(), m.end())
    depth = 0
    closing = -1
    for i in range(opening, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                closing = i
                break
    if closing < 0:
        raise RuntimeError("Unclosed use() method: " + rel)
    block = s[m.start():closing + 1]
    block = re.sub(
        r"public\s+(?:net\.minecraft\.util\.)?ActionResult\s+use\s*\(",
        "public net.minecraft.util.TypedActionResult<net.minecraft.item.ItemStack> use(",
        block,
    )
    block = re.sub(
        r"return\s+ActionResult\.SUCCESS\s*;",
        "return net.minecraft.util.TypedActionResult.success(user.getStackInHand(hand));",
        block,
    )
    block = re.sub(
        r"return\s+ActionResult\.PASS\s*;",
        "return net.minecraft.util.TypedActionResult.pass(user.getStackInHand(hand));",
        block,
    )
    s = s[:m.start()] + block + s[closing + 1:]
    p.write_text(s, encoding="utf-8", newline="\n")

patch_use("src/main/java/com/blenderphysics/item/RealisticFluidBucketItem.java")
patch_use("src/main/java/com/blenderphysics/item/RealityWandItem.java")

p = root / "src/main/java/com/blenderphysics/entity/PhysicsRigidBodyEntity.java"
s = p.read_text(encoding="utf-8")
s, count = re.subn(
    r"public\s+net\.minecraft\.network\.packet\.Packet\s*<\s*net\.minecraft\.network\.listener\.ClientPlayPacketListener\s*>\s+createSpawnPacket\s*\(\s*\)\s*\{\s*return\s+new\s+EntitySpawnS2CPacket\(this\);\s*\}",
    "public net.minecraft.network.packet.Packet<net.minecraft.network.listener.ClientPlayPacketListener> createSpawnPacket(net.minecraft.server.network.EntityTrackerEntry entityTrackerEntry) {\n\t\treturn new EntitySpawnS2CPacket(this, entityTrackerEntry);\n\t}",
    s,
)
if count != 1:
    raise RuntimeError("Expected one old createSpawnPacket method, found " + str(count))
p.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/main/java/com/blenderphysics/config/BlenderPhysicsConfig.java"
s = p.read_text(encoding="utf-8")
s = s.replace("public int maxParticles = 8000;", "public int maxParticles = 2500;")
s = s.replace("public int simulationRadius = 32;", "public int simulationRadius = 24;")
s = s.replace("public WaterShaderQuality waterShaderQuality = WaterShaderQuality.ULTRA_BLENDER;", "public WaterShaderQuality waterShaderQuality = WaterShaderQuality.MEDIUM;")
s = s.replace("public int physicsSubsteps = 2;", "public int physicsSubsteps = 1;")
s = s.replace("public float foamAmount = 0.05f;", "public float foamAmount = 0.005f;")
s = s.replace("foamAmount = clamp(foamAmount, 0.0f, 0.30f);", "foamAmount = clamp(foamAmount, 0.0f, 0.02f);")
p.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/client/java/com/blenderphysics/client/gui/BlenderPhysicsConfigScreen.java"
s = p.read_text(encoding="utf-8").replace("0.0, 0.30, cfg.foamAmount", "0.0, 0.02, cfg.foamAmount")
p.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/client/resources/assets/blenderphysics/shaders/core/fluid_composite.fsh"
s = p.read_text(encoding="utf-8")
s = s.replace("clamp(foamMask * FoamAmount * 6.0, 0.0, 0.35)", "clamp(foamMask * FoamAmount * 1.0, 0.0, 0.02)")
s = s.replace("alpha <= 0.35", "alpha <= 0.02")
p.write_text(s, encoding="utf-8", newline="\n")

p = root / "src/client/resources/assets/blenderphysics/shaders/core/fluid_composite.json"
if p.exists():
    obj = json.loads(p.read_text(encoding="utf-8"))
    for u in obj.get("uniforms", []):
        if u.get("name") == "FoamAmount":
            u["values"] = [0.005]
    p.write_text(json.dumps(obj, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")

for rel in ["src/main/resources/assets/blenderphysics/lang/es_es.json", "src/main/resources/assets/blenderphysics/lang/en_us.json"]:
    p = root / rel
    data = json.loads(p.read_text(encoding="utf-8"))
    for key in [
        "item.blenderphysics.water_bomb",
        "item.blenderphysics.lava_bomb",
        "item.blenderphysics.slime_bomb",
    ]:
        data.pop(key, None)
    es = rel.endswith("es_es.json")
    data["blenderphysics.config.sim_radius"] = "Radio visual: %s bloques" if es else "Visual Range: %s blocks"
    data["blenderphysics.config.quality.ultra"] = "Alto (hasta 3000 partículas)" if es else "High (up to 3000 particles)"
    data["blenderphysics.config.quality.medium"] = "Equilibrado (hasta 1800 partículas)" if es else "Balanced (up to 1800 particles)"
    data["blenderphysics.config.quality.low"] = "Ligero (hasta 900 partículas)" if es else "Lightweight (up to 900 particles)"
    p.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")

write("src/client/java/com/blenderphysics/client/render/FluidRenderPipeline.java", """package com.blenderphysics.client.render;

import com.blenderphysics.config.BlenderPhysicsConfig;
import com.blenderphysics.config.WaterShaderQuality;
import com.blenderphysics.physics.FluidParticleBuffer;
import com.blenderphysics.physics.FluidSimulationWorld;
import com.blenderphysics.physics.FluidType;
import com.blenderphysics.physics.PhysicsManager;
import com.mojang.blaze3d.systems.RenderSystem;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.BufferBuilder;
import net.minecraft.client.render.BufferRenderer;
import net.minecraft.client.render.GameRenderer;
import net.minecraft.client.render.Tessellator;
import net.minecraft.client.render.VertexFormat;
import net.minecraft.client.render.VertexFormats;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Vec3d;
import net.minecraft.client.util.math.MatrixStack;
import org.joml.Matrix4f;

/**
 * Renders only particles created by BlenderPhysics.
 * Vanilla oceans, rivers, lakes and source-water blocks are never replaced or
 * automatically converted. Render cost is capped by quality, particle budget,
 * and visual radius.
 */
public final class FluidRenderPipeline {
    private static final float[][] OCTA_VERTICES = {
            {0f, 1f, 0f}, {0f, -1f, 0f}, {-1f, 0f, 0f},
            {1f, 0f, 0f}, {0f, 0f, -1f}, {0f, 0f, 1f}
    };
    private static final int[] OCTA_FACES = {
            0, 2, 5,  0, 5, 3,  0, 3, 4,  0, 4, 2,
            1, 5, 2,  1, 3, 5,  1, 4, 3,  1, 2, 4
    };

    private FluidRenderPipeline() {}

    public static void register() {
        WorldRenderEvents.AFTER_TRANSLUCENT.register(FluidRenderPipeline::onAfterTranslucent);
    }

    private static void onAfterTranslucent(WorldRenderContext context) {
        MinecraftClient client = MinecraftClient.getInstance();
        if (client.world == null || client.player == null || client.getServer() == null) return;

        ServerWorld serverWorld = client.getServer().getWorld(client.world.getRegistryKey());
        if (serverWorld == null) return;

        FluidSimulationWorld simulation = PhysicsManager.get().simulationFor(serverWorld);
        FluidParticleBuffer particles = simulation.buffer();
        if (particles.activeCount() == 0) return;

        BlenderPhysicsConfig cfg = BlenderPhysicsConfig.get();
        int qualityLimit = switch (cfg.waterShaderQuality) {
            case LOW -> 900;
            case MEDIUM -> 1800;
            case ULTRA_BLENDER -> 3000;
        };
        int drawLimit = Math.min(cfg.maxParticles, qualityLimit);
        renderParticleBodies(context, particles, simulation.worldKey(), cfg.simulationRadius, drawLimit);
    }

    private static void renderParticleBodies(WorldRenderContext context, FluidParticleBuffer particles,
                                             long worldKey, int renderRadius, int drawLimit) {
        MatrixStack matrices = context.matrixStack();
        if (matrices == null) return;

        Vec3d camera = context.camera().getPos();
        double radiusSq = (double) renderRadius * renderRadius;
        matrices.push();
        matrices.translate(-camera.x, -camera.y, -camera.z);
        Matrix4f positionMatrix = matrices.peek().getPositionMatrix();

        BufferBuilder buffer = Tessellator.getInstance().begin(
                VertexFormat.DrawMode.TRIANGLES, VertexFormats.POSITION_COLOR);

        RenderSystem.enableBlend();
        RenderSystem.defaultBlendFunc();
        RenderSystem.enableDepthTest();
        RenderSystem.depthMask(false);
        RenderSystem.disableCull();
        RenderSystem.setShader(GameRenderer::getPositionColorProgram);

        int rendered = 0;
        for (int i = 0; i < particles.highWaterMark() && rendered < drawLimit; i++) {
            if (!particles.active[i] || particles.worldSeed[i] != worldKey) continue;

            double dx = particles.posX[i] - camera.x;
            double dy = particles.posY[i] - camera.y;
            double dz = particles.posZ[i] - camera.z;
            if (dx * dx + dy * dy + dz * dz > radiusSq) continue;

            FluidType type = FluidType.byId(particles.type[i]);
            float radius = type == FluidType.LAVA ? 0.105f : 0.12f;
            float[] color = baseColor(type);
            float centerX = particles.posX[i];
            float centerY = particles.posY[i];
            float centerZ = particles.posZ[i];

            for (int vertexIndex : OCTA_FACES) {
                float[] v = OCTA_VERTICES[vertexIndex];
                float highlight = 0.88f + 0.12f * Math.max(0f, v[1]);
                buffer.vertex(positionMatrix,
                        centerX + v[0] * radius,
                        centerY + v[1] * radius,
                        centerZ + v[2] * radius)
                        .color(color[0] * highlight, color[1] * highlight, color[2] * highlight, color[3]);
            }
            rendered++;
        }

        if (rendered > 0) {
            BufferRenderer.drawWithGlobalProgram(buffer.end());
        }

        RenderSystem.depthMask(true);
        RenderSystem.enableCull();
        RenderSystem.disableBlend();
        matrices.pop();
    }

    private static float[] baseColor(FluidType type) {
        return switch (type) {
            case WATER -> new float[] {0.08f, 0.46f, 0.68f, 0.78f};
            case LAVA -> new float[] {0.95f, 0.25f, 0.035f, 0.95f};
            case SLIME -> new float[] {0.16f, 0.72f, 0.25f, 0.82f};
        };
    }
}
""")

p = root / "README.md"
if p.exists():
    s = p.read_text(encoding="utf-8")
    note = "\n\n## Agua personalizada y rendimiento\n\nBlenderPhysics dibuja únicamente las partículas creadas por el propio mod (cubos realistas, varita y emisores). No reemplaza los bloques de agua vanilla ni convierte automáticamente océanos, ríos, lagos ni fuentes naturales. La calidad limita la cantidad de partículas dibujadas; el límite total, el radio visual y los subpasos reducen la carga. La espuma queda casi desactivada por defecto y su control está limitado a valores muy bajos.\n"
    if "## Agua personalizada y rendimiento" not in s:
        p.write_text(s + note, encoding="utf-8", newline="\n")

# Stop if any stale bomb registration survived.
java = "\n".join(p.read_text(encoding="utf-8") for p in (root / "src").rglob("*.java"))
for stale in ["WATER_BOMB_ENTITY", "LAVA_BOMB_ENTITY", "SLIME_BOMB_ENTITY", "ModItems.WATER_BOMB", "new FluidBombItem"]:
    if stale in java:
        raise RuntimeError("Stale registration reference: " + stale)

print("PATCH_OK")
