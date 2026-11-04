/**
 * Players and ball. Pure D3, zero React imports.
 *
 * Encoding (DESIGN.md): defenders filled blue; defenders upfield of the ball pale with a blue ring;
 * attackers hollow ink; keepers square in their team's style; the player on the ball gets an ink
 * halo; the ball is white with an ink ring and sits on top.
 *
 * 360 freeze-frames have no player identities, so dots can't be tracked between frames. The
 * group crossfades on each frame instead of sliding dots between unrelated players.
 */
import type * as d3 from 'd3'
import type { FrameData, PlayerPosition } from '../../types/frame'
import { frameDuration, PITCH_THEME as T } from './theme'

type G = d3.Selection<SVGGElement, unknown, null, undefined>

const R = 1.55

export function renderPlayers(g: G, frame: FrameData, animate: boolean) {
  g.selectAll('*').remove()
  // Actor last so its halo sits above neighbours.
  const players = [...frame.players].sort((a, b) => Number(a.actor) - Number(b.actor))

  for (const p of players) {
    if (p.actor) {
      g.append('circle')
        .attr('cx', p.x).attr('cy', p.y).attr('r', R + 1.1)
        .attr('fill', 'none').attr('stroke', T.ink).attr('stroke-width', 1.25)
        .attr('vector-effect', 'non-scaling-stroke')
    }
    drawPlayer(g, p, frame.ball_x)
  }

  g.append('circle')
    .attr('cx', frame.ball_x).attr('cy', frame.ball_y).attr('r', 0.95)
    .attr('fill', T.ball).attr('stroke', T.ink).attr('stroke-width', 1.5)
    .attr('vector-effect', 'non-scaling-stroke')

  const ms = animate ? frameDuration() : 0
  if (ms > 0) {
    g.interrupt().attr('opacity', 0.35).transition().duration(ms).attr('opacity', 1)
  } else {
    g.interrupt().attr('opacity', 1)
  }
}

function ring<E extends SVGElement>(sel: d3.Selection<E, unknown, null, undefined>, color: string, width: number) {
  sel.attr('stroke', color).attr('stroke-width', width).attr('vector-effect', 'non-scaling-stroke')
}

function drawPlayer(g: G, p: PlayerPosition, ballX: number) {
  if (p.keeper) {
    ring(
      g.append('rect')
        .attr('x', p.x - R).attr('y', p.y - R).attr('width', R * 2).attr('height', R * 2).attr('rx', 0.7)
        .attr('fill', p.is_attacker ? T.canvas : T.defence),
      p.is_attacker ? T.ink : T.canvas,
      p.is_attacker ? 2 : 1.5,
    )
    return
  }
  if (p.is_attacker) {
    ring(g.append('circle').attr('cx', p.x).attr('cy', p.y).attr('r', R - 0.1).attr('fill', T.canvas), T.ink, 2)
    return
  }
  const upfield = p.x >= ballX
  ring(
    g.append('circle')
      .attr('cx', p.x).attr('cy', p.y).attr('r', upfield ? R - 0.1 : R)
      .attr('fill', upfield ? T.defenceSoft : T.defence),
    upfield ? T.defence : T.canvas,
    1.5,
  )
}
