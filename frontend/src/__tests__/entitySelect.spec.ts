import { flushPromises, mount } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { describe, expect, it } from 'vitest'

import EntitySelect from '@/components/common/EntitySelect.vue'

interface Team {
  id: string
  name: string
  members?: string[]
}

function mountSelect(initial: Team | null) {
  return mount(EntitySelect<Team>, {
    props: {
      modelValue: initial?.id ?? null,
      fetcher: async () => ({ items: [{ id: 'a', name: 'Alpha', members: ['x'] }], count: 1 }),
      label: (team: Team) => team.name,
      initial,
    },
  })
}

describe('EntitySelect', () => {
  it('shows the initial record although the list does not contain it', async () => {
    const wrapper = mountSelect({ id: 'b', name: 'Beta' })
    await flushPromises()
    const options = wrapper.findComponent(NSelect).props('options') as {
      label: string
      value: string
    }[]
    expect(options.map((o) => o.label)).toEqual(['Beta', 'Alpha'])
  })

  it('hands out only records loaded from the list', async () => {
    const wrapper = mountSelect({ id: 'b', name: 'Beta' })
    await flushPromises()
    const select = wrapper.findComponent(NSelect)
    select.vm.$emit('update:value', 'a')
    select.vm.$emit('update:value', 'b')
    expect(wrapper.emitted('select')).toEqual([
      [{ id: 'a', name: 'Alpha', members: ['x'] }],
      [null],
    ])
  })
})
