import styled from '@emotion/styled'

export const TableContainer = styled.div`
  position: relative;
  width: 100%;
  overflow: hidden;
  .table {
    display: block;
  }
  .sort-icon:not(.sorted) {
    opacity: 0;
  }
  .thead {
    position: sticky;
    top: 0;
    z-index: 1;
  }
  .tbody-scroll-box {
    position: relative;
    overflow: scroll;
  }
  .tbody {
    display: flex;
    flex-direction: column;
    width: 100%;
  }
  .tr {
  display: flex;
  flex-grow: 1;
  flex-shrink: 0;
  min-width: 100%;
  }
  .th {
    position: relative;
    line-height: 24px;
    white-space: nowrap;
    user-select: none;
    text-align: left;
    background-color: var(--base-bg);
    width: 300px;
    font-weight: 500;
    overflow: hidden;
    &:hover .sort-icon {
      opacity: 1;
    }
    &.column-actions {
      background-color: var(--base-bg);
      z-index: 10;
    }
  }
  .th-text {
    width: calc(100% - 32px);
    flex-shrink: 1;
    overflow: hidden;
    span {
      vertical-align: middle;
      display: inline-block;
      width: 100%;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  .td {
    border-bottom: 1px solid ${x => x.theme.colors.grey};
    font-size: 14px;
    background-color: var(--base-bg);
    display: flex;
    align-items: center;
    span {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    &.column-actions {
      box-shadow: var(--actions-column-shadow);
    }
  }
  .text-right {
    text-align: right;
    justify-content: flex-end;
  }
  .column-actions {
    position: sticky;
    right: 0;
    .th-text {
      width: fit-content;
    }
  }
  .column-id {
    .th-text {
      width: fit-content;
    }
  }
  .td, .th {
    padding: 8px 16px;
    height: 48px;
    &.compact {
      padding: 2px 8px;
      height: 36px;
    }
  }
`
