import {ReactNode, useEffect, useRef, useState} from 'react';
import styled from '@emotion/styled';
import {useRadio, useRadioGroup} from '@react-aria/radio';
import {RadioGroupState, useRadioGroupState} from '@react-stately/radio';
import {AriaRadioGroupProps, AriaRadioProps} from '@react-types/radio';

import space from 'sentry/styles/space';
import {defined} from 'sentry/utils';

type Option = {
  label: string;
  value: string;
};
type RadioBarProps = AriaRadioGroupProps & {
  options: Option[];
  moveLeft?: boolean;
};

type HandleStyles = {left: number; width: number};
type HandleLookup = Record<string, HandleStyles>;

const RadioBar = ({moveLeft, ...props}: RadioBarProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const state = useRadioGroupState(props);
  const {radioGroupProps} = useRadioGroup(props, state);
  const [handleStyles, setHandleStyles] = useState<HandleStyles>({left: 0, width: 0});
  const [handleLookup, setHandleLookup] = useState<HandleLookup>({});

  /**
   * Initialize lookup table (handleLookup) that describes the position
   * of each render radio element, useful for animating <Handle />
   */
  useEffect(() => {
    setTimeout(() => {
      const handleLookupTable: HandleLookup = {};
      (ref.current?.childNodes as NodeListOf<HTMLElement>)?.forEach(
        (node: HTMLElement) => {
          const radioValue = node.dataset?.radioValue;
          if (!radioValue) {
            return;
          }
          handleLookupTable[radioValue] = {
            left: node.offsetLeft,
            width: node.offsetWidth,
          };
        }
      );
      setHandleLookup(handleLookupTable);
    }, 100);
  }, []);

  useEffect(() => {
    setHandleStyles(handleLookup[state.selectedValue as keyof HandleLookup]);
  }, [handleLookup, state.selectedValue]);

  return (
    <GroupWrap moveLeft={moveLeft} {...radioGroupProps} ref={ref}>
      {props.options.map((option, i) => (
        <Radio
          key={option.value}
          state={state}
          nextValue={props.options[i + 1]?.value}
          lastValue={props.options[props.options.length - 1].value}
          {...option}
        >
          {option.label}
        </Radio>
      ))}
      <Handle {...handleStyles} />
    </GroupWrap>
  );
};

type RadioProps = AriaRadioProps &
  Option & {
    children: ReactNode;
    lastValue: string;
    state: RadioGroupState;
    nextValue?: string;
  };

const Radio = ({lastValue, nextValue, state, ...props}: RadioProps) => {
  const ref = useRef<HTMLInputElement>(null);
  const {inputProps} = useRadio(props, state, ref);
  const isSelected = state.selectedValue === props.value;
  const isLastOption = props.value === lastValue;
  const nextOptionIsSelected = state.selectedValue === nextValue;

  return (
    <RadioWrap isSelected={isSelected} data-radio-value={props.value}>
      <RadioInput {...inputProps} ref={ref} />
      <HiddenChildren aria-hidden="true">{props.children}</HiddenChildren>
      <VisibleChildren isSelected={isSelected}>{props.children}</VisibleChildren>
      <Divider
        visible={!isSelected && !nextOptionIsSelected && !isLastOption}
        role="separator"
        aria-orientation="vertical"
      />
    </RadioWrap>
  );
};

export default RadioBar;

const GroupWrap = styled('div')<{moveLeft?: boolean}>`
  position: relative;
  display: inline-flex;
  background: ${p => p.theme.backgroundSecondary};
  border: solid 1px ${p => p.theme.border};
  border-radius: ${p => p.theme.borderRadius};

  ${p => p.moveLeft && `transform: translateX(-${space[0]})`}
`;

const Handle = styled('div')<{left?: number; width?: number}>`
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: ${p => p.theme.background};
  border-radius: calc(${p => p.theme.borderRadius} - 1px);
  box-shadow: ${p => p.theme.dropShadowLight};
  opacity: 0;
  transition: transform 0.25s ease-out, width 0.25s ease-out, opacity 0.25s ease-out;

  ${p =>
    defined(p.left) &&
    defined(p.width) &&
    `
    opacity: 1;
    transform: translateX(${p.left}px);
    width: ${p.width}px;
  `}

  @media (prefers-reduced-motion) {
    display: none;
  }
`;

const RadioWrap = styled('label')<{isSelected: boolean}>`
  position: relative;
  display: block;
  margin: 0;
  padding: ${space(1)} ${space(2)};
  border-radius: calc(${p => p.theme.borderRadius} - 1px);
  cursor: pointer;

  font-weight: 400;
  color: ${p => p.theme.subText};

  &:hover {
    background-color: ${p => p.theme.hover};

    [role='separator'] {
      opacity: 0;
    }
  }

  ${p =>
    p.isSelected &&
    `
    z-index: 1;
    transition: background-color 0.25s ease-out;

    &:hover {
      background-color: transparent;
    }
  `}
`;

const HiddenChildren = styled('span')`
  visibility: hidden;
  user-select: none;
`;

const VisibleChildren = styled('span')<{isSelected: boolean}>`
  position: absolute;
  top: 50%;
  left: 50%;
  width: max-content;
  transform: translate(-50%, -50%);
  transition: color 0.25s ease-out;

  ${p =>
    p.isSelected &&
    `
    color: ${p.theme.activeText};
    font-weight: 600;
  `}
`;

const Divider = styled('div')<{visible: boolean}>`
  position: absolute;
  top: 50%;
  right: 0;
  width: 0;
  height: 50%;
  transform: translate(1px, -50%);
  border-right: solid 1px ${p => p.theme.innerBorder};

  ${p => !p.visible && `opacity: 0;`}
`;

const RadioInput = styled('input')`
  appearance: none;
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  padding: 0;
  margin: 0 1px;
  border-radius: ${p => p.theme.borderRadius};
  transition: box-shadow 0.125s ease-out;
  z-index: -1;
`;
