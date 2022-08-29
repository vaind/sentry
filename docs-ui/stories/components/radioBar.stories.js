import RadioBar1 from 'sentry/components/radioBar1';
import RadioBar2 from 'sentry/components/radioBar2';
import RadioBar3 from 'sentry/components/radioBar3';

export default {
  title: 'Components/RadioBar',
  parameters: {
    controls: {hideNoControlsWarning: true},
  },
};

export const _RadioBar = () => (
  <div>
    <h6>#1</h6>
    <RadioBar1
      text="0"
      defaultValue="opt_1"
      options={[
        {value: 'opt_1', label: 'Opt 1'},
        {value: 'opt_2', label: 'Opt 2'},
        {value: 'opt_3', label: 'Opt 3'},
      ]}
    />
    <br />
    <br />
    <br />
    <h6>#2</h6>
    <RadioBar2
      text="0"
      defaultValue="opt_1"
      options={[
        {value: 'opt_1', label: 'Opt 1'},
        {value: 'opt_2', label: 'Opt 2'},
        {value: 'opt_3', label: 'Opt 3'},
      ]}
    />
    <br />
    <br />
    <br />
    <h6>#3</h6>
    <RadioBar3
      text="0"
      defaultValue="opt_1"
      options={[
        {value: 'opt_1', label: 'Opt 1'},
        {value: 'opt_2', label: 'Opt 2'},
        {value: 'opt_3', label: 'Opt 3'},
      ]}
    />
  </div>
);

_RadioBar.parameters = {
  docs: {},
};
